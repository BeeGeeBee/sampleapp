CREATE TABLE Components(
ID	integer primary key,
Name	Varchar(50),
Description	Varchar(250),
CategoriesID	integer,
SuppliersID	integer,
CurrentStock	integer,
ReorderLevel	integer,
LocationsID	integer,
Datasheet	Varchar(250),
OrderCode	varchar(50),
UnitPrice	float
);