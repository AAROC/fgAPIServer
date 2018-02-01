# FutureGateway API Server front-end (fgAPIServer)
[![Travis](http://img.shields.io/travis/FutureGateway/geAPIServer/master.png)](https://travis-ci.org/FutureGateway/geAPIServer)
[![License](https://img.shields.io/github/license/FutureGateway/geAPIServer.svg?style?flat)](http://www.apache.org/licenses/LICENSE-2.0.txt)

This project implements the interface of a RESTful API Server, compliant with [CSGF APIs][specs] specifications. Any activity processed by this interface will be then processed by the [API Server Daemon][APIServerDaemon] component.
The principal aim of this component is to accept incoming REST APIs, verify user rights and provide back a result. Some APIs require to fill a queue table which will be processed by the APIServerDaemon component. 

   [specs]: <http://docs.csgfapis.apiary.io/#reference/v1.0/application/create-a-task>
   [CSGF]: <https://www.catania-science-gateways.it>
   [API Server Daemon]: <https://github.com/FutureGateway/APIServerDaemon>
