# La-Cosa
Implementación sobre interfaz web del juego de cartas La Cosa.

## Instalación
1. Descargar el repositorio.
```
$ git clone https://github.com/IS1-NombreGenerico/La-Cosa.git
```
2. Entrar a la carpeta descargada.
```
$ cd La-Cosa/src
```
3. Crear un entorno virtual con python (Debe ser con python 3.10).
```
$ python -m venv venv-LaCosa
```
ó
```
$ python3.10 -m venv venv-LaCosa
```

4. Ejecutar el entorno virtual.
```
$ source venv-LaCosa/bin/activate
```
5. Instalar los requerimientos.

```
$ pip install -r ../requirements.txt
```

## Correr base de datos
1. Correr uvicorn
```
$ uvicorn hello:app --reload
```

## Correr tests
1. Eliminar la base de datos si la hay
```
$ rm *.sqlite3
```
ó
```
$ rm *.sqlite
```
2. Correr los tests respectivos con `mark` de pytest
```
$ pytest -v -m integration_test
```
ó
```
$ python3 -m pytest -v -m integration_test              
```
