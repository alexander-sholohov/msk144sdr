## MSK144 Web SDR Server and Spot Reporter.

### Brief documentation:

The project is a Flask based web server. You can run it in development mode as:
```shell
flask run
```

The application utilizes sqlite database. One time creation process:
```shell
python init_db.py  
```

Folder **utils** contains banch of utilities to build datapath between SDR devices, [msk144 decoder](https://github.com/alexander-sholohov/msk144cudecoder) and this web server. If necessary, datapath can be splitted to different machines in the Net. Each utility accepts something on stdin, does its job and produces something to stdout. Invoke them with --help to get brief info.


Live example:
http://sdr.22dx.ru/msk144/


Alexander, RA9YER.  
ra9yer@yahoo.com
