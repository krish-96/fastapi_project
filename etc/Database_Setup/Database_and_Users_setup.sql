-- 1. Login as root
mysql -u root -p

-- 2. Create the application database
CREATE DATABASE fastapi_app
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

--Verify:

SHOW DATABASES;

--3. Switch to the database
USE fastapi_app;

--4. Create users
--Admin User
--Can perform everything within this database.

CREATE USER 'fastapi_admin'@'%' IDENTIFIED BY 'password';
-- Developer User

--Can create tables, indexes, alter schema, insert/update/delete data.

CREATE USER 'fastapi_dev'@'%' IDENTIFIED BY 'password!';

--Read-only User

--Useful for reporting, BI, analytics, dashboards.

CREATE USER 'fastapi_readonly'@'%' IDENTIFIED BY 'password!';

--5. Grant permissions
--Admin
GRANT ALL PRIVILEGES
ON fastapi_app.*
TO 'fastapi_admin'@'%';
--Developer
--Notice we intentionally do not grant user management or global privileges.

GRANT
SELECT,
INSERT,
UPDATE,
DELETE,
CREATE,
ALTER,
DROP,
INDEX,
CREATE VIEW,
SHOW VIEW,
CREATE TEMPORARY TABLES,
LOCK TABLES,
REFERENCES,
TRIGGER
ON fastapi_app.*
TO 'fastapi_dev'@'%';
--Read-only
GRANT
SELECT,
SHOW VIEW
ON fastapi_app.*
TO 'fastapi_readonly'@'%';

--6. Apply privileges
FLUSH PRIVILEGES;
--7. Verify
SELECT user, host
FROM mysql.user;

--Check grants:

SHOW GRANTS FOR 'fastapi_admin'@'%';

SHOW GRANTS FOR 'fastapi_dev'@'%';

SHOW GRANTS FOR 'fastapi_readonly'@'%';
--8. Test each user

--Admin

mysql -u fastapi_admin -p fastapi_app

--Developer

mysql -u fastapi_dev -p fastapi_app

--Readonly

mysql -u fastapi_readonly -p fastapi_app
--Security Best Practices
--1. Never use root from your application

-- #############################################################

-- ❌ DATABASE_URL = "mysql+pymysql://root:password@mysql/fastapi_app"

-- ✅ DATABASE_URL = "mysql+pymysql://fastapi_admin:password@mysql/fastapi_app"
-- #############################################################

--2. Use different accounts
-- #############################################################
--    Purpose	                            User
--FastAPI application	    fastapi_admin (or a more restricted app user)
--Alembic migrations  	fastapi_dev or a dedicated fastapi_migrator
--Reporting/BI    	    fastapi_readonly
--DBA         	        root
-- #############################################################
-- A further improvement is to create a dedicated fastapi_app user for the application that has only DML permissions (SELECT, INSERT, UPDATE, DELETE, EXECUTE) and reserve fastapi_dev for schema changes.

-- #############################################################
