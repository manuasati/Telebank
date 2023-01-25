function myFunction() {
   var sh = SpreadsheetApp.getActiveSpreadsheet();
  const sheet_name="All_data_305389645"
  var row_start=2;
  var diff;
  var arr2=[{}];
  var myString2=SpreadsheetApp.getActiveSheet().getRange(row_start,5).getValue();
  var myString3 = myString2.toString();
 
  arr2 = myString3.split("/");

  var first_row_value=arr2[0];
  var sheet = SpreadsheetApp.getActiveSheet();
  var data = sheet.getDataRange().getValues();
  //  Logger.log(data[1])
  var l = data.length;
  var value=data[l-1];
  var value1=value[4];

  var repeat;
  
  // Logger.log(value1)

  for(var first_row_value1=first_row_value;first_row_value1<=value1;first_row_value1++)
  {
    var arr1=[{}];
    var current_value1 = SpreadsheetApp.getActiveSheet().getRange(row_start,5).getValue();
    var myString = current_value1.toString();

    // Logger.log(myString)

    arr1 = myString.split("/");
    current_value2=arr1[0];

    Logger.log(current_value2)

    if(first_row_value1==current_value2 )

    { 
      
      sh.getSheetByName(sheet_name).getRange(row_start,5).setBackground("white");
      
      }
      

    
     else
    { 

      if(repeat==current_value2)
      {
        sh.getSheetByName(sheet_name).getRange(row_start-1,5).setBackground("red");
        sh.getSheetByName(sheet_name).getRange(row_start,5).setBackground("red");
      }

      else
      {
      diff=current_value2 - first_row_value1;

      sh.getSheetByName(sheet_name).getRange(row_start,5).setBackground("orange");

      first_row_value1=first_row_value1+diff;
      repeat=first_row_value1;
      }

    }
    row_start++;

  }
}