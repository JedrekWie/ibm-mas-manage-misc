# Miscellaneous IBM MAS Manage Utilities

## Automation Scripts

### Export Message Tracking Data

The [EXPORTMSGTRACKING.py](./autoscript/EXPORTMSGTRACKING.py) script exports *Message Tracking* data from the `MAXINTMSGTRK` table. The data to be exported is selected based on a set of restrictions provided as query parameters in a REST API call.

#### Supported REST API query parameters

* `msgId` - message ID (`MAXINTMSGTRK.MEAMSGID`) of the message to export (supports exact or SQL wildcard matching)
* `extSys` - external system name (`MAXINTMSGTRK.EXTSYSNAME`) of the message to export (supports exact or SQL wildcard matching)
* `iface` - publish channel or enterprise service name (`MAXINTMSGTRK.IFACENAME`) of the message to export (supports exact or SQL wildcard matching)
* `sfData` - search field data (`MAXINTMSGTRK.SEARCHFIELDDATA`) of the message to export (supports exact or SQL wildcard matching)
* `daysAge` - number of days back in time (since now) when the message to be exported was received/sent (`MAXINTMSGTRK.INITIALDATETIME`)
* `query` - any additional SQL where clause for the `MAXINTMSGTRK` table to filter messages for export
* `limit` - limit number of messages to be exported; if not specified then the default limit of `1000` messages is applied
* `prettyPrint` - when set to `1` or `true` then JSON and/or XML messages are pretty printed before exporting
* `addExpInfo` - when set to `1` or `true` causes an `export-info.txt` file with details about the request input and output to be included in the result archive

**NOTE:** All parameters restricting `MAXINTMSGTRK` data can be used at the same time. In such case resulting selection where clause will contain appropriate database table column criteria joined with **AND** logical operator.

#### Example usage

**Example #1**

```bash
curl --location 'http://<host>:<port>/maxrest/api/script/EXPORTMSGTRACKING?msgId=1496496.1736947899816251893' \
--header 'APIKEY: <apikey>'
```

Exports tracked message data of message ID equal to `1496496.1736947899816251893`.

**NOTE:** `addExpInfo` request parameter has not been specified, the same result as if it has been specified and its value is true (`1` or `true`), therefore result ZIP archive contains `export-info.txt` of following example content:
```
Exported Message Tracking Data
==============================
Export Date and Time: 2025-02-25 12:35:38
Where clause: (msgdata is not null) AND (meamsgid like '1496496.1736947899816251893')
Total Records: 1
Execution Time: 1 s
```

**Example #2**

```bash
curl --location 'http://<host>:<port>/maxrest/api/script/EXPORTMSGTRACKING?extSys=DATALOAD&iface=MXASSET' \
--header 'APIKEY: <apikey>'
```

Exports tracked message data sent/received using `DATALOAD` external system **and** `MXASSET` publish channel/enterprise service.

**Example #3**

```bash
curl --location 'http://<host>:<port>/maxrest/api/script/EXPORTMSGTRACKING?sfData=WO123%' \
--header 'APIKEY: <apikey>'
```

Exports tracked message data with *Search ID* **starting with** `WO123`.

**Example #4**

```bash
curl --location 'http://<host>:<port>/maxrest/api/script/EXPORTMSGTRACKING?daysAge=5' \
--header 'APIKEY: <apikey>'
```

Exports tracked message data received/sent within the range of last 5 days.

**Example #4**

```bash
curl --location 'http://<host>:<port>/maxrest/api/script/EXPORTMSGTRACKING?daysAge=5' \
--header 'APIKEY: <apikey>'
```

Exports tracked message data received/sent within the range of last 5 days.

**Example #5**

```bash
curl --location 'http://<host>:<port>/maxrest/api/script/EXPORTMSGTRACKING?query=status%20%3D%20%27RECEIVED%27' \
--header 'APIKEY: <apikey>'
```

Exports tracked message data matching explicitly provided `query` parameter (`status = 'RECEIVED'`).