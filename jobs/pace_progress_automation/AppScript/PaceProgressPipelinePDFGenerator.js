function fetchDocumentId(timeline) {
  switch (timeline) {
    case "90 Day":
      return "1OI4LO9PvmP35DJIaTWXDTXUfanIl1WloJWGSaHwibWo";
    case "120 Day":
      return "1q2wazDzYd9KskGfZT6267GzYlAmwE_-Z0UawfSrQyUA";
    case "180 Day":
      return "1nCQkguA8KaOfAkIT7dRFamspXOhTFM3zYeR2A9BXUH8";
    case "365 Day":
      return "1EjIo4LqzTZg-27umDtV3-R8nkObHTXVeARMcmj7B1Q8";
    default:
      return "ERROR";
  }
}

function replaceBodyTextFromArgs(body, argDict) {
  body.replaceText("{full_name}", argDict.full_name);
  body.replaceText("{enrollment_date}", argDict.enrollment_date);

  switch (argDict.timeline) {
    case "90 Day":
      body.replaceText("{week_4}", argDict.week_4);
      body.replaceText("{week_9}", argDict.week_9);
      body.replaceText("{week_13}", argDict.week_13);
      break;
    case "120 Day":
      body.replaceText("{week_4}", argDict.week_4);
      body.replaceText("{week_6}", argDict.week_6);
      body.replaceText("{week_7}", argDict.week_7);
      body.replaceText("{week_12}", argDict.week_12);
      body.replaceText("{week_18}", argDict.week_18);
      break;
    case "180 Day":
      body.replaceText("{week_6}", argDict.week_6);
      body.replaceText("{week_7}", argDict.week_7);
      body.replaceText("{week_8}", argDict.week_8);
      body.replaceText("{week_9}", argDict.week_9);
      body.replaceText("{week_10}", argDict.week_10);
      body.replaceText("{week_18}", argDict.week_18);
      body.replaceText("{week_26}", argDict.week_26);
      break;
    case "365 Day":
      body.replaceText("{week_6}", argDict.week_6);
      body.replaceText("{week_9}", argDict.week_9);
      body.replaceText("{week_10}", argDict.week_10);
      body.replaceText("{week_12}", argDict.week_12);
      body.replaceText("{week_13}", argDict.week_13);
      body.replaceText("{week_14}", argDict.week_14);
      body.replaceText("{week_15}", argDict.week_15);
      body.replaceText("{week_16}", argDict.week_16);
      body.replaceText("{week_17}", argDict.week_17);
      body.replaceText("{week_18}", argDict.week_18);
      body.replaceText("{week_19}", argDict.week_19);
      body.replaceText("{week_34}", argDict.week_34);
      body.replaceText("{week_52}", argDict.week_52);
      break;
  }
  body.replaceText("{week_1}", argDict.week_1);
  body.replaceText("{week_2}", argDict.week_2);
  body.replaceText("{week_3}", argDict.week_3);
  body.replaceText("{week_5}", argDict.week_5);
  return body;
}

function createDocument(args) {
  var argDict = JSON.parse(args);

  var TEMPLATE_ID = fetchDocumentId(argDict.timeline);
  var documentId = DriveApp.getFileById(TEMPLATE_ID).makeCopy().getId();

  var driveDoc = DriveApp.getFileById(documentId);
  driveDoc.setName(argDict.file_name);

  doc = DocumentApp.openById(documentId);

  body = replaceBodyTextFromArgs(doc.getBody(), argDict);
  driveDoc.setSharing(
    DriveApp.Access.ANYONE_WITH_LINK,
    DriveApp.Permission.EDIT
  );

  return (
    "https://docs.google.com/document/d/" + documentId + "/export?format=pdf"
  );
}

function doGet(e) {
  var url = createDocument(e.parameter.args);
  return ContentService.createTextOutput(url);
}
