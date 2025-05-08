	

--=============================================================================================================================	
	
1.- Liste a aquellos empleados que han cambiado de puesto (basta con colocar el identificador).


SELECT (employee_id)
FROM job_history;
---7 EMPLOYEES ID EN JOB_HISTORY
select distinct(employee_id) 	as employee
	,job_id		as puesto
from job_history
MINUS
select employee_id 	as employee
	,job_id		as puesto
from employees
order by 1;

SELECT employee_id, job_id AS puesto
FROM job_history
GROUP BY employee_id,job_id
MINUS
SELECT employee_id, job_id  AS puesto
FROM employees
GROUP BY employee_id,job_id
ORDER BY 1;

--=============================================================================================================================	
2.- Se desea conocer a aquellos empleados nunca han cambiado de puesto en la Empresa, el reporte deberá presentar identificador 
	de Empleado.

SELECT DISTINCT(EMPLOYEE_ID)
FROM JOB_HISTORY;--7 

SELECT EMPLOYEE_ID
FROM EMPLOYEES
MINUS
SELECT EMPLOYEE_ID
FROM JOB_HISTORY;
--100 FILAS

  
--=============================================================================================================================  
3.- Muestre el historial de puestos de los TODOS los empleados, Su reporte puede deberá listar el identificador del empleado
	y el identificador del puesto. Ordene su consulta por identificador de empleado.

 -- Se refiere a todos los registros de job_history? por ejemplo hay 2 empleados que tienen el mismo puesto 
SELECT EMPLOYEE_ID AS EMPLEADO
	,NVL(TO_CHAR(JOB_ID),'SIN HISTORIAL DE PUESTO')	AS HISTORIAL
FROM EMPLOYEES
UNION 
SELECT EMPLOYEE_ID AS EMPLEADO
	,TO_CHAR(JOB_ID)
FROM JOB_HISTORY
ORDER BY 1 ASC;
--115 filas

--=============================================================================================================================

4.- Actualice el reporte anterior, de manera que se observe en su listado, cual es el puesto actual y el/los puestos anteriores
	del empleado.

SELECT EMPLOYEE_ID AS EMPLEADO
	,NVL(TO_CHAR(JOB_ID),'SIN HISTORIAL DE PUESTO')	AS HISTORIAL
FROM EMPLOYEES
UNION ALL
SELECT EMPLOYEE_ID AS EMPLEADO
	,TO_CHAR(JOB_ID)
FROM JOB_HISTORY
ORDER BY 1 ASC;
--117 filas




--=============================================================================================================================
5.- Actualice el reporte anterior, colocando la fecha en la que el empleado dejo de laborar con el puesto; lo anterior
	únicamente en los puestos anteriores.
 

SELECT EMPLOYEE_ID AS EMPLEADO
	,NVL(TO_CHAR(JOB_ID),'SIN HISTORIAL DE PUESTO')	AS HISTORIAL
	,' '	AS "F.FINAL"
FROM EMPLOYEES
UNION ALL
SELECT EMPLOYEE_ID AS EMPLEADO
	,TO_CHAR(JOB_ID)
	,To_char(TO_DATE(END_DATE,'DD/MM/YY')) 
FROM JOB_HISTORY
ORDER BY 1 ASC;
  
--=============================================================================================================================  
6.- Cree un informe que muestre el Identificador de empleado, 
	así como el identificador de Puesto de aquellos empleados que 
	han tenido su puesto actual en algún otro periodo laboral.


SELECT EMPLOYEE_ID AS EMPLEADO
	,JOB_ID  AS PUESTO
FROM EMPLOYEES
INTERSECT
SELECT EMPLOYEE_ID 
	,JOB_ID  
FROM JOB_HISTORY;

--=============================================================================================================================
 
7.- Actualice el reporte anterior e incluya el nombre del puesto 
	de aquellos empleados que han tenido su puesto actual 
	en algún otro periodo laboral.

	
SELECT EMPLOYEE_ID AS EMPLEADO
	,JOB_ID AS "ID.PUESTO"
	,JOB_TITLE AS PUESTO
FROM EMPLOYEES
NATURAL JOIN JOBS
INTERSECT
SELECT EMPLOYEE_ID
	,JOB_ID
	,JOB_TITLE
FROM JOB_HISTORY
NATURAL JOIN JOBS;
	 

 
--=============================================================================================================================
8.- Genere el historial de puestos del empleado con 
	identificador 101 y 176; mostrando en su reporte cual 
	es el puesto actual y cuales fueron en su caso los anteriores.
	Ordene su consulta por medio del ID del empleado.
 
SELECT EMPLOYEE_ID AS EMPLEADO
	,JOB_ID AS PUESTO
FROM EMPLOYEES
WHERE EMPLOYEE_ID IN(101,176)
UNION ALL 
SELECT EMPLOYEE_ID
	,JOB_ID AS PUESTO
FROM JOB_HISTORY
WHERE EMPLOYEE_ID IN(101,176)
ORDER BY 1 ASC;
 --6 FILAS 
 
--=============================================================================================================================	
9.- El departamento de recursos humanos necesita el listado 
	de aquellos departamentos (basta con el identificador de 
	departamento) que no tengan a empleados con el puesto ST_CLERK, 
	es decir si un departamento tiene a algún empleado con 
	dicho puesto, el departamento no debe aparecer en el informe.




 

 
--=============================================================================================================================	 
10.- Se desea conocer a aquellos empleados han cambiado de puesto 
	en la Empresa, el reporte deberá presentar identificador de 
	Empleado y nombre de este.

SELECT EMPLOYEE_ID AS EMPLEADO
	,JOB_TITLE AS PUESTO_ANTERIOR
FROM JOB_HISTORY
NATURAL JOIN JOBS
MINUS
SELECT EMPLOYEE_ID
	,JOB_TITLE
FROM EMPLOYEES
NATURAL JOIN JOBS;	
	
	
	
--=============================================================================================================================

11.- Muestre a aquellos empleados que han cambiado de puesto 
	 en el mismo departamento, el reporte deberá mostrar 
	 el identificador de empleado y el identificador de
	departamento en cuestión.

SELECT EMPLOYEE_ID AS EMPLEADO
	,DEPARTMENT_ID AS DEPTO
FROM JOB_HISTORY
INTERSECT
SELECT EMPLOYEE_ID
	,DEPARTMENT_ID
FROM EMPLOYEES;
 
 

--=============================================================================================================================	 
12.-  El departamento de recursos humanos necesita una lista de países que no tienen ningún departamento. Muestre el ID de 
      país y el nombre de los países. Utilice los operadores de definición para crear este informe.

ALTER TABLE HR.DEPARTMENTS ADD COUNTRY_ID  CHAR(2);
ALTER TABLE  HR.DEPARTMENTS ADD COUNTRY_NAME VARCHAR2(40) ;


SELECT DATA_DEFAULT, COLUMN_NAME
  FROM USER_TAB_COLUMNS
 WHERE TABLE_NAME = <TableName> 
  AND DATA_DEFAULT IS NOT NULL;
  
UPDATE DEPARTMENTS D
SET COUNTRY_ID = (
  SELECT L.COUNTRY_ID
  FROM LOCATIONS L
  WHERE L.LOCATION_ID = D.LOCATION_ID
);

UPDATE DEPARTMENTS D
SET COUNTRY_NAME = (
  SELECT L.COUNTRY_NAME
  FROM COUNTRIES L
  WHERE L.COUNTRY_ID = D.COUNTRY_ID
);	


SELECT COUNTRY_ID AS "ID.PAIS",
	COUNTRY_NAME "PAIS"
FROM departmets;
minus
SELECT COUNTRY_ID AS,
	COUNTRY_NAME
FROM countries;
-- 25 filas

 
 

	 
	 
	 