USE PERSONDATABASE

/*********************
Hello! 

Please use the test data provided in the file 'PersonDatabase' to answer the following
questions. Please also import the dbo.Contacts flat file to a table for use. 

All answers should be executable on a MS SQL Server 2012 instance. 

***********************/

/*  SQl to create Contacts table */

USE PersonDatabase
GO


CREATE TABLE dbo.Contracts
(
	PersonID INT
	, ContractStartDate DATETIME
	, ContractEndDate DATETIME
)



/*
QUESTION 1

The table dbo.Risk contains calculated risk scores for the population in dbo.Person. Write a 
query or group of queries that return the patient name, and their most recent risk level(s). 
Any patients that dont have a risk level should also be included in the results. 

**********************/

/*There are some people with two risk scores for different payers at the same time. I listed both in those cases if they were the most recent*/

select p.personid,p.personname,max(r.RiskDateTime) LatestRiskDate
INTO #MaxRisk
from person p
left join risk r on p.PersonID=r.PersonID
group by p.personid,p.personname

Select m.PersonName, r.RiskScore
from risk r
inner join #MaxRisk m on m.PersonID=r.PersonID and m.LatestRiskDate=r.RiskDateTime

drop table #MaxRisk



/**********************

QUESTION 2


The table dbo.Person contains basic demographic information. The source system users 
input nicknames as strings inside parenthesis. Write a query or group of queries to 
return the full name and nickname of each person. The nickname should contain only letters 
or be blank if no nickname exists.

**********************/

select personname,
LTrim(  
	Replace(
		Replace(
			personname,	SUBSTRING(personname, CHARINDEX('(', personname), CHARINDEX(')',personname) - CHARINDEX('(',personname) + Len(')')) 
			,'')
	,')','')
) as fullname,
Replace(SUBSTRING(personname, CHARINDEX('(', personname)+1, CHARINDEX(')',personname) - CHARINDEX('(',personname) + Len(')')-1),
	')','') as nickname
from person


/**********************

QUESTION 6

Write a query to return risk data for all patients, all payers 
and a moving average of risk for that patient and payer in dbo.Risk. 

**********************/




SELECT  personid, attributedpayer, riskscore, riskdatetime,
   ROW_NUMBER() OVER (
      PARTITION BY personid, attributedpayer
      ORDER BY personid, attributedpayer, riskdatetime
   ) row_num
   INTO #RowNumbers
FROM 
 risk
ORDER BY 
personid, attributedpayer,riskdatetime


SELECT rn.personid, rn.attributedpayer, rn.riskscore,rn.riskdatetime, 
        CASE
            WHEN rn.row_num =1 THEN rn.RiskScore
            ELSE (  SELECT  avg(RiskScore) 
                    FROM    #RowNumbers
                    WHERE   row_num <= rn.row_num
                    AND    #RowNumbers.AttributedPayer = rn.AttributedPayer
					AND   #RowNumbers.Personid= rn.PersonID 
                )
        END AS MovingAverage
FROM   #RowNumbers rn
order by rn.personid, rn.AttributedPayer

Drop Table #RowNumbers
