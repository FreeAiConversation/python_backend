import win32com.client
import os
import sys

def convert_pdf_to_excel(pdf_path, excel_path):
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    try:
        # Open PDF in Word (Word natively converts PDF to editable format)
        print("Opening PDF in Word...")
        doc = word.Documents.Open(FileName=os.path.abspath(pdf_path), ConfirmConversions=False, ReadOnly=True)
        
        # Save as Single File Web Page (mht) or HTML (wdFormatHTML = 8, wdFormatFilteredHTML = 10)
        html_path = os.path.abspath("temp_doc.htm")
        print(f"Saving as HTML to {html_path}...")
        doc.SaveAs2(FileName=html_path, FileFormat=8)
        doc.Close(False)
        
        # Open HTML in Excel
        print("Opening HTML in Excel...")
        wb = excel.Workbooks.Open(html_path)
        
        # Save as XLSX (xlOpenXMLWorkbook = 51)
        print(f"Saving as XLSX to {excel_path}...")
        wb.SaveAs(FileName=os.path.abspath(excel_path), FileFormat=51)
        wb.Close(False)
        
        if os.path.exists(html_path):
            os.remove(html_path)
        if os.path.exists(html_path.replace(".htm", "_files")):
            import shutil
            shutil.rmtree(html_path.replace(".htm", "_files"), ignore_errors=True)
            
        print("Conversion complete!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        word.Quit()
        excel.Quit()

if __name__ == "__main__":
    if len(sys.argv) == 3:
        convert_pdf_to_excel(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python test_convert.py input.pdf output.xlsx")
