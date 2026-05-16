import win32com.client
import os

excel = win32com.client.DispatchEx("Excel.Application")
excel.Visible = False
wb = excel.Workbooks.Add()
ws = wb.ActiveSheet

# Create some formatted cells
ws.Range("A1").Value = "Test Table"
ws.Range("A1:C1").Merge()
ws.Range("A1").Interior.Color = 12566463 # Some grey color
ws.Range("A1").Font.Bold = True

ws.Range("A2").Value = "Col 1"
ws.Range("B2").Value = "Col 2"
ws.Range("C2").Value = "Col 3"

ws.Range("A3").Value = "Data 1"
ws.Range("B3").Value = "Data 2"
ws.Range("C3").Value = "Data 3"

# Apply borders to A1:C3
for border_id in [7,8,9,10,11,12]: # EdgeTop, EdgeBottom, EdgeLeft, EdgeRight, InsideVertical, InsideHorizontal
    ws.Range("A1:C3").Borders(border_id).LineStyle = 1
    ws.Range("A1:C3").Borders(border_id).Weight = 2

pdf_path = os.path.abspath("test_input.pdf")
wb.ExportAsFixedFormat(0, pdf_path)
wb.Close(False)
excel.Quit()

print(f"Created {pdf_path}")
