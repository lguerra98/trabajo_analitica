/*Al subir las tablas a bigquery nombrar como rawcondiciones_vida, rawsuicidios, rawviolen_intfam y establecer el esquema de todas las vasriables como string*/

CREATE TABLE rawcondiciones_vida (
localidad VARCHAR(25),
condiciones VARCHAR(25),
porcentaje NUMERIC);

CREATE TABLE rawsuicidios(
area VARCHAR(100),
ano INTEGER NOT NULL,
grupo_edad VARCHAR(25),
sexo VARCHAR(15) CHECK(sexo LIKE 'Hombre' OR sexo LIKE 'Mujer'),
casos INTEGER);

CREATE TABLE rawviolen_intfam(
ano INTEGER NOT NULL,
area VARCHAR(20),
type_violen VARCHAR(25),
sexo VARCHAR(20) CHECK(LOWER(TRIM(sexo)) LIKE 'hombre' OR LOWER(TRIM(sexo)) LIKE 'mujer' OR LOWER(TRIM(sexo)) LIKE 'total general'),
n_casos INTEGER,
poblacion INTEGER,
tasa_x100h NUMERIC);

/*CONSULTAS BIGQUERY*/

/*Guardar los resultados de las siguientes consultas en tablas de bigquery como violen_intfam, suicidios, condiciones_vida */
SELECT EXTRACT(YEAR FROM CAST(SUBSTRING(ano,1,4) AS DATE FORMAT 'YYYY')) AS ano, area, type_violen, TRIM(sexo) AS sexo, CAST(REPLACE(n_casos, '.', '')AS numeric) AS n_casos, CAST(REPLACE(poblacion, '.', '')AS int64) AS poblacion, CAST(REPLACE(tasa_x100h, ',', '.') AS float64) AS tasa_x100h FROM `sunlit-inn-353723.trabajo_final_analitica.rawviolen_intfam`
GROUP BY ano, area, type_violen, sexo, n_casos, poblacion, tasa_x100h
ORDER BY ano, sexo DESC, type_violen;


SELECT area, EXTRACT(YEAR FROM CAST(SUBSTRING(ano,1,4) AS DATE FORMAT 'YYYY')) AS ano, grupo_edad, sexo, CAST(casos AS INT64) AS casos FROM `sunlit-inn-353723.trabajo_final_analitica.rawsuicidios`
GROUP BY ano, grupo_edad, area, sexo, casos
ORDER BY ano, area, sexo, grupo_edad;

SELECT localidad, condiciones, CAST(REPLACE(porcentaje, ',', '.') AS NUMERIC) AS porcentaje FROM `sunlit-inn-353723.trabajo_final_analitica.rawcondiciones_vida`
GROUP BY localidad, condiciones, porcentaje
ORDER BY localidad DESC;

/*1. ¿Cuál es el porcentaje promedio de personas que perciben una condición de vida buena y muy buena en todas las localidades?*/
SELECT condiciones, AVG(porcentaje) AS porcentaje_promedio
FROM `analiticanegocios1.Salud.condiciones_vida`
GROUP BY condiciones
HAVING condiciones = "Bueno" OR condiciones = "Muy Bueno";

/*2. ¿Cuál es la cantidad total de hombres que han sufrido violencia emocional?*/
SELECT * FROM `sunlit-inn-353723.analiticanegocios1.Salud.violen_intfam`)
SELECT sexo, SUM(n_casos) AS total_sex, type_violen FROM violen_intfam
WHERE type_violen LIKE 'Emocional' AND area != 'Distrito'
GROUP BY sexo, type_violen
HAVING sexo = 'Hombre';

/*3. ¿Cuál es el mayor tipo de violencia que ocurre en la localidad con mayor porcentaje de percepción de vida muy mala?*/
SELECT t1.localidad, t1.condiciones, t1.porcentaje, SUM(n_casos) AS total_typ, t2.type_violen FROM(SELECT * FROM `analiticanegocios1.Salud.condiciones_vida`
WHERE condiciones LIKE 'Muy Malo'
ORDER BY porcentaje DESC
LIMIT 1) t1
INNER JOIN `analiticanegocios1.Salud.violen_intfam` t2
ON t1.localidad = t2.area
GROUP BY type_violen, localidad, condiciones, porcentaje
ORDER BY total_typ DESC
LIMIT 1;

/*4.¿Cuál es la cantidad de casos de suicidio por sexo en la localidad con mayor poblacion en el 2020?*/
SELECT t1.ano, t1.area, t2.sexo, t1.poblacion, t2.casos FROM (SELECT DISTINCT ano, area, sexo, poblacion FROM `analiticanegocios1.Salud.violen_intfam`
WHERE ano = 2020 AND sexo LIKE 'Tot%' AND area NOT LIKE 'Distrito'
ORDER BY poblacion DESC
LIMIT 1) t1
INNER JOIN (SELECT * FROM `analiticanegocios1.Salud.suicidios`
WHERE grupo_edad LIKE 'Todos los grupos'
ORDER BY area, ano, grupo_edad, sexo) t2
ON t1.area = t2.area
WHERE t2.ano = 2020;

/*5.¿Cuáles son las 5 localidades con mayor puntaje entre la suma de la percepción de vida mala y muy mala?*/
SELECT localidad, SUM(porcentaje) AS suma_worst FROM `analiticanegocios1.Salud.condiciones_vida`
WHERE condiciones IN ('Malo', 'Muy Malo') 
GROUP BY localidad
ORDER BY suma_worst DESC
LIMIT 5;

/*6.¿Cuál es la cantidad de casos de suicidio en pesonas entre los 15 y 24 años por sexo a partir del 2020?*/
SELECT sexo, '15 a 24' AS grupo_edad, SUM(casos) AS total  FROM `analiticanegocios1.Salud.suicidios`
WHERE ano >= 2020 AND REGEXP_CONTAINS(grupo_edad, r'([12][1-9]|20) a (1[4-9]|2[0-4])') AND area NOT LIKE 'Dis%'
GROUP BY sexo, grupo_edad;

/*7.¿Cuáles son los porcentajes de condiciones de vida de la localidad con mayor tasa por 100 mil habitantes de casos de violencia intrafamiliar en el año 2019?*/
SELECT t1.area, t2.condiciones, t2.porcentaje, t1.tasa_x100h FROM (SELECT * FROM `analiticanegocios1.Salud.violen_intfam`
WHERE sexo LIKE 'To%' AND type_violen LIKE 'Intr%' AND ano = 2019
ORDER BY tasa_x100h DESC
LIMIT 1) t1
INNER JOIN `analiticanegocios1.Salud.condiciones_vida` t2
ON LOWER(t1.area) = LOWER(t2.localidad);


/*8.¿Cuál es el porcentaje de la condición de vida (malo y muy malo) de la localidad con mayor número de casos de suicidio entre 2015 y 2017?*/
SELECT t1.area, t2.condiciones, t2.porcentaje FROM(SELECT area, SUM(casos) AS total FROM `analiticanegocios1.Salud.suicidios`
WHERE ano BETWEEN 2015 AND 2017 AND grupo_edad LIKE 'Tod%'
GROUP BY area
HAVING area NOT LIKE 'Dis%'
ORDER BY total DESC
LIMIT 1) t1
INNER JOIN `analiticanegocios1.Salud.condiciones_vida` t2
ON LOWER(t1.area) = LOWER(t2.localidad)
WHERE condiciones IN ('Malo', 'Muy Malo');

/*9.¿Cuál es el tipo de violencia con mayor ocurrencia por localidad en cada año?*/
SELECT t1.ano, t1.area, t1.sexo, t2.type_violen, t1.maximo  FROM(SELECT ano, area, sexo, MAX(n_casos) AS maximo FROM `analiticanegocios1.Salud.violen_intfam`
WHERE area NOT LIKE 'Dis%' 
GROUP BY ano, area,sexo
ORDER BY area) t1
INNER JOIN (SELECT ano, area, type_violen, sexo, n_casos FROM `analiticanegocios1.Salud.violen_intfam`
WHERE type_violen NOT LIKE 'Intr%') t2
ON t1.ano = t2.ano AND t1.area = t2.area AND t1.sexo = t2.sexo AND t1.maximo = t2.n_casos;

/*10.¿Cuál es el año donde ocurrieron mayor cantidad de suicidios?*/
SELECT ano, grupo_edad, SUM(casos) AS total FROM `analiticanegocios1.Salud.suicidios`
WHERE area LIKE 'Dis%' AND grupo_edad LIKE 'Todo%'
GROUP BY ano, grupo_edad
ORDER BY total DESC
LIMIT 1;

/*11.¿Cuáles son los 3 rangos de edad en los que más se suicidan las mujeres?*/
SELECT grupo_edad, SUM(casos) AS total FROM `analiticanegocios1.Salud.suicidios`
WHERE grupo_edad NOT LIKE 'Tod%'AND area LIKE 'Dis%' AND sexo LIKE 'Mujer'
GROUP BY grupo_edad
ORDER BY total DESC
LIMIT 3;

/*12.¿Cuántas personas tienen condiciones de vida buenas en la localidad de Usme para el año 2017 en el que se realiza la encuesta? */
SELECT ano, localidad, condiciones, (poblacion * (porcentaje/100)) AS total
FROM(SELECT DISTINCT ano, area, poblacion FROM `analiticanegocios1.Salud.violen_intfam`
WHERE ano = 2017 AND area = 'Usme' AND sexo LIKE 'To%') t1
INNER JOIN `analiticanegocios1.Salud.condiciones_vida` t2
ON t1.area = t2.localidad
WHERE condiciones IN ('Bueno','Muy Bueno');

/*13.¿Cuántos casos de abandono hay en total en la ciudad de Bogotá?*/
SELECT  type_violen, sum(n_casos) AS TOTAL
FROM `analiticanegocios1.Salud.violen_intfam`
WHERE area <> "Distrito" AND type_violen = 'Abandono'
GROUP BY type_violen;

/*14.¿Cuántas personas durante el 2015 hasta el 2019 se suicidaron entre los 15 y los 29 años de edad?*/
SELECT "2015 - 2019" ano, "15 - 29" grupo_edad, SUM(casos) AS total_casos_suicidio
FROM `analiticanegocios1.Salud.suicidios`
WHERE (ano  BETWEEN (2015) AND (2019)) AND REGEXP_CONTAINS(grupo_edad, r'([12][1-9]|20) a (1[4-9]|2[0-9])') AND area <>"Distrito";

/*15.¿Cuál es el tipo de violencia que tiene mayores casos en la ciudad de Usaquén?*/
SELECT area, type_violen, sum(n_casos) AS TOTAL
FROM `analiticanegocios1.Salud.violen_intfam`
WHERE area = "Usaquén"
GROUP BY type_violen, area
ORDER BY TOTAL DESC 
LIMIT 1;
