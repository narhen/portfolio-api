# Portfolio API
[![Build Status](https://travis-ci.org/narhen/portfolio-api.svg?branch=master)](https://travis-ci.org/narhen/portfolio-api)


## Running tests
```
$ python -m unittest discover
```

## Building docker image
```
$ docker build -t portfolio-api .
```

## Running docker container
```
$ docker run --env-file vars.env --link mysql --name portfolio-api -d -p 5000:5000 portfolio-api
```
