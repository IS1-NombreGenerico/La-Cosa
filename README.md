# La-Cosa
Implementación sobre interfaz web del juego de cartas La Cosa.

## Instalación
Se necesitara previamente tener venv.

1. Descargar el repositorio.
2. Entrar a la carpeta descargada.
3. Crear un entorno virtual con python (Debe ser con python 3.10).
4. Ejecutar el entorno virtual.
5. Instalar los requerimientos.

```
$ git clone https://github.com/IS1-NombreGenerico/La-Cosa.git
$ cd La-Cosa
$ python -m venv venv-LaCosa
$ source venv-LaCosa/bin/activate
$ pip install -r requirements.txt
```

## Correr tests

1. Eliminar la base de datos si la hay
2. Correr los tests respectivos con `mark` de pytest

Ejemplo con `mark` integration_test
```
$ rm *.sqlite3
$ pytest -v -m integration_test
```