from java.lang import System
from java.util.concurrent import TimeUnit
from java.util import Date
from java.io import ByteArrayOutputStream
from java.util.zip import ZipEntry, ZipOutputStream
from psdi.iface.jms import MessageUtil
from psdi.iface.mic import MicUtil
from psdi.iface.util import XMLUtils
from psdi.server import MXServer
from psdi.mbo import SqlFormat
from psdi.util import CombineWhereClauses
import time

# Global variables
logPrefix = u"[EXPORTMSGTRACKING]"

# Get the MAXINTMSGTRK table where clause based on the input parameters
def getWhereClause(extSys, iface, msgId, sfData, daysAge, query):
    service.log(u"{} BEGIN getWhereClause".format(logPrefix))
    mxs = MXServer.getMXServer()
    ui = mxs.getSystemUserInfo()

    cwc = CombineWhereClauses("msgdata is not null")
    if extSys is not None:
        sqf = SqlFormat(ui, "extsysname like :1")
        sqf.setObject(1, "MAXEXTSYSTEM", "EXTSYSNAME", extSys)
        cwc.addWhere(sqf.format())
    if iface is not None:
        sqf = SqlFormat(ui, "ifacename like :1")
        sqf.setObject(1, "MAXIFACEIN", "IFACENAME", iface)
        cwc.addWhere(sqf.format())
    if msgId is not None:
        sqf = SqlFormat(ui, "meamsgid like :1")
        sqf.setObject(1, "MAXINTMSGTRK", "MEAMSGID", msgId)
        cwc.addWhere(sqf.format())
    if sfData is not None:
        sqf = SqlFormat(ui, "searchfielddata like :1")
        sqf.setObject(1, "MAXINTMSGTRK", "SEARCHFIELDDATA", sfData)
        cwc.addWhere(sqf.format())
    if daysAge is not None:
        dateAge = Date(System.currentTimeMillis() - TimeUnit.DAYS.toMillis(daysAge))
        sqf = SqlFormat(ui, "initialdatetime > :1")
        sqf.setDate(1, dateAge)
        cwc.addWhere(sqf.format())
    if query is not None:
        cwc.addWhere(query)

    whereClause = cwc.getWhereClause()
    service.log(u"{} END getWhereClause -> {}".format(logPrefix, whereClause))
    return whereClause
# end getWhereClause

def addExportInfoZipEntry(zos, whereClause, count, execTime):
    service.log(u"{} addExportInfoZipEntry -> {}b / {}s".format(
        logPrefix, count, execTime))
    zos.putNextEntry(ZipEntry("export-info.txt"))
    currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    info = """Exported Message Tracking Data
    ==============================
    Export Date and Time: {}
    Where clause: {}
    Total Records: {}
    Execution Time: {} s
    """.format(currentTime, whereClause, count, execTime)
    # Dedent the info string
    info = "\n".join(line.strip() for line in info.splitlines())
    zos.write(info.encode('utf-8'))
    zos.closeEntry()
# end addExportInfoZipEntry

# Add a new ZIP entry of given name to the ZIP output stream
def addZipEntry(zos, name, data):
    service.log(u"{} addZipEntry -> {}".format(logPrefix, name))
    zos.putNextEntry(ZipEntry(name))
    zos.write(data)
    zos.closeEntry()
# end addZipEntry

# Get the response body as a ZIP file containing the message tracking data
def getResponseBody(whereClause, prettyPrint, addExportInfo):
    service.log(u"{} BEGIN getResponseBody".format(logPrefix))

    mxs = MXServer.getMXServer()
    ui = mxs.getSystemUserInfo()
    msgTrkSet = mxs.getMboSet("MAXINTMSGTRK", ui)

    execTime = 0
    # Create a byte array output stream to hold the ZIP file data
    os = ByteArrayOutputStream()
    zos = ZipOutputStream(os)
    
    try:
        startTime = time.time()
        msgTrkSet.setWhere(whereClause)
        count = msgTrkSet.count()
        service.log(u"{} COUNT -> {}".format(logPrefix, count))

        msgTrk = msgTrkSet.moveFirst()
        i = 1
        while msgTrk is not None:
            msgId = msgTrk.getString("meamsgid")
            service.log(u"{} #{}\tMEAMSGID -> {}".format(logPrefix, i, msgId))

            meaMsgId = msgTrk.getString("meamsgid")
            extSys = msgTrk.getString("extsysname")
            iface = msgTrk.getString("ifacename")
            msgData = msgTrk.getBytes("msgdata")
            length = msgTrk.getInt("msglength")
            mimeType = msgTrk.getString("mimetype")

            byteData = MessageUtil.uncompressMessage(msgData, length)

            fileName = "{}_{}_{}".format(extSys, iface, meaMsgId)
            fileExt = { 
                "application/json": "json",
                "application/xml": "xml",
            }.get(mimeType, "txt")
            
            # Attempt to pretty print the data if it is JSON or XML
            # and prettyPrint is enabled
            if prettyPrint:
                try:
                    if mimeType == "application/json":
                        byteData = MicUtil.prettyPrintJSON(byteData).encode('utf-8')
                    elif mimeType == "application/xml":
                        doc = XMLUtils.convertBytesToDocument(byteData)
                        byteData = XMLUtils.convertDocumentToBytes(doc)
                except Exception as e:
                    service.log_warn(u"{} Failed to pretty print {} ({}) -> {}".format(
                        logPrefix, msgId, mimeType, e))

            addZipEntry(zos, "{}.{}".format(fileName, fileExt), byteData)

            i += 1
            msgTrk = msgTrkSet.moveNext()
        # end while

        endTime = time.time()
        execTime = int(endTime - startTime)
        if addExportInfo:
            addExportInfoZipEntry(zos, whereClause, count, execTime)
    finally:
        if msgTrkSet:
            msgTrkSet.close()
        if zos:
            zos.close()
        if os:
            os.close()

    # Return the ZIP file as an array of bytes    
    responseBody = os.toByteArray()
    service.log(u"{} END getResponseBody -> {}b / {}s".format(
        logPrefix, len(responseBody), execTime ))
    return responseBody
# end getResponseBody

# Main
service.log(u"{} BEGIN".format(logPrefix))
responseHeaders.put('content-type', 'application/zip')

extSys = request.getQueryParam("extSys")
iface = request.getQueryParam("iface")
msgId = request.getQueryParam("msgId")
sfData = request.getQueryParam("sfData")
daysAge = int(request.getQueryParam("daysAge")) if request.getQueryParam("daysAge") else None
query = request.getQueryParam("query")
prettyPrint = request.getQueryParam("prettyPrint") not in ["false", "0"]
addExportInfo = request.getQueryParam("addExpInfo") not in ["false", "0"]
service.log(u"""{} PARAMS -> [extSys={}] [iface={}] [msgId={}]\
     [sfData={}] [daysAge={}] [query={}] [addExpInfo={}]
    """.format(logPrefix, extSys, iface, msgId, sfData, daysAge, query, addExportInfo))

whereClause = getWhereClause(extSys, iface, msgId, sfData, daysAge, query)
responseBody = getResponseBody(whereClause, prettyPrint, addExportInfo)
service.log(u"{} END".format(logPrefix))

scriptConfig="""{
    "autoscript": "EXPORTMSGTRACKING",
    "description": "Extract Message Tracking",
    "version": "",
    "active": true,
    "logLevel": "INFO"
}"""