import pyodbc
import xlrd
from datetime import datetime

conn = pyodbc.connect("DRIVER={SQL SERVER};Server=LAUREN\SQLEXPRESS;Database=PersonDatabase;Trusted_Connection=yes;")
file_path = r"C:\Users\lblasch\Downloads\senior_engineer_assessment-master\senior_engineer_assessment-master\PythonTestQuestions\Privia Family Medicine 113018.xlsx"
book = xlrd.open_workbook(file_path)
sheet = book.sheet_by_name("Sheet1")

# QUESTION 1
# Import the 'Demographics' data section to a table in the database. This ETL will need to process files of the same type delivered later on with different file dates and from different groups.


# Parse the Date from the file name and convert to datetime format
FileDateString = file_path.split(" ")[-1]
FileDateString = FileDateString.replace('.xlsx', '', 1)
FileDate = datetime.strptime(FileDateString, '%m%d%y')

# Parse the Provider Group name from the file name
ProviderGroupName = file_path.split("\\")[-1]
ProviderGroupName = ProviderGroupName.rsplit(' ', 1)[0]

# I used the below for Testing
# print(FileDateString)
print(FileDate)
print(ProviderGroupName)

cursor = conn.cursor()

# Checks to see if Demographic table exists and if so drop it. Can comment out this step if we want to build on existing data.
cursor.execute( "IF EXISTS	(SELECT 1 FROM SYS.Tables WHERE NAME = 'Demographics'	) DROP TABLE Demographics	; CREATE TABLE dbo.Demographics (	ProviderGroup varchar(255),	DateofFile DATE, PatientId VARCHAR(255),	FirstName VARCHAR(255),	MiddleName VARCHAR(255),LastName VARCHAR(255),	DOB DATETIME, 	Sex VARCHAR(255),FavoriteColor VARCHAR(255))")
conn.commit()
print("Demographics Table Created.")

# Below Steps are to append data from the excel spreadsheet to SQL Server Database
query_ImportData = """INSERT INTO dbo.Demographics (ProviderGroup,DateofFile,PatientId, FirstName, MiddleName, LastName, DOB, Sex, FavoriteColor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""

# Start at row 5 to exclude headers
for r in range(4, sheet.nrows):

    # If the patient id is null then stop  any further rows.
    if sheet.cell(r, 1).value == '':
        break

    ProviderGroup = ProviderGroupName  # Defined above based on file name
    DateofFile = FileDate  # Defined above based on file name
    PatientId = sheet.cell(r, 1).value
    FirstName = sheet.cell(r, 2).value
    MiddleName = sheet.cell(r, 3).value[:1]  # Only take the first character of the middle name. (Question 1d)
    LastName = sheet.cell(r, 4).value
    DOB = sheet.cell(r, 5).value
    Sex = sheet.cell(r, 6).value
    FavoriteColor = sheet.cell(r, 7).value

    values = (ProviderGroup, DateofFile,PatientId, FirstName, MiddleName, LastName, DOB, Sex, FavoriteColor)

    cursor.execute(query_ImportData, values)

print("Data Loaded to Demographics")



# Addresses question 1e
query_UpdateSex = """ Update Demographics Set Sex='M' where Sex ='0'; Update Demographics Set Sex='F' Where Sex='1';"""
cursor.execute(query_UpdateSex)
conn.commit()

print("Updated Sex Field")

# QUESTION 2
# Transform and import the 'Quarters' and 'Risk' data into a separate table.

#Staging table to import data from excel before unpivoting the data
cursor.execute("""IF EXISTS	(SELECT 1 FROM SYS.Tables WHERE NAME = 'Staging_RiskbyQuarter' ) DROP TABLE dbo.Staging_RiskbyQuarter	; CREATE TABLE dbo.Staging_RiskbyQuarter (Id varchar(255), AttributedQ1 varchar(255),	AttributedQ2 Varchar(255),	RiskQ1 Decimal(20,18) , RiskQ2 Decimal(20,18) , RiskIncreasedFlag VARCHAR(255)	, FileDate DATE);IF EXISTS	(SELECT 1 FROM SYS.Tables WHERE NAME = 'RiskbyQuarter' ) DROP TABLE dbo.RiskbyQuarter	; CREATE TABLE dbo.RiskbyQuarter (	Id varchar(255),	Quarter Varchar(255), AttributedFlag VARCHAR(255),	RiskScore Decimal(20,18) ,	FileDate DATE )""")
conn.commit()

print("Risk Tables Created")
query_ImportQuarterlyData = """INSERT INTO dbo.Staging_RiskbyQuarter (Id, AttributedQ1, AttributedQ2, RiskQ1, RiskQ2, RiskIncreasedFlag, FileDate) VALUES (?, ?, ?, ?, ?, ?, ?)"""

# Start at row 5 to exclude headers
for r in range(4, sheet.nrows):

    # If the patient id is null then stop  any further rows.
    if sheet.cell(r, 1).value == '':
        break

    Id = sheet.cell(r, 1).value
    AttributedQ1 = sheet.cell(r, 8).value
    AttributedQ2 = sheet.cell(r, 9).value
    RiskQ1 = sheet.cell(r, 10).value
    RiskQ2 = sheet.cell(r, 11).value
    RiskIncreasedFlag = sheet.cell(r, 12).value
    DateofFile = FileDate  # Defined above based on file name

    values = (Id, AttributedQ1, AttributedQ2, RiskQ1, RiskQ2, RiskIncreasedFlag, FileDate)

    cursor.execute(query_ImportQuarterlyData, values)
conn.commit()
print("Data Loaded to Staging Table")


#Unpivot
# Unpivot table INTO Table For Question 2 and only include records with the risk increased flag set to True
query_UnPivot = """
        INSERT INTO RiskByQuarter
        SELECT	DISTINCT 
        Id,
        Replace (QuarterNum, 'Attributed','') Quarter,
        QuarterAttributed AS AttributedFlag,
        Risk as RiskScore,
        FileDate
        FROM  Staging_RiskbyQuarter
        UNPIVOT ( [QuarterAttributed] FOR [QuarterNum] 
          IN ([AttributedQ1],[AttributedQ2]) )
        AS Risk1
        UNPIVOT ( [Risk] FOR [QuarterNum1] 
          IN ([RiskQ1],[RiskQ2]) )
        AS Risk2
        WHERE riskincreasedflag='Yes' 
        AND 
        Replace (QuarterNum, 'Attributed','') = Replace (QuarterNum1, 'Risk','') 
        """

cursor.execute(query_UnPivot)

conn.commit()



cursor.close()

conn.close()

print("Done")