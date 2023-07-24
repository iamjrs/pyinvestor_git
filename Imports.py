from websocket import WebSocket, WebSocketApp, create_connection, _exceptions
from multiprocessing.pool import ThreadPool
from urllib.parse import urlencode, quote, unquote
from klepto.archives import file_archive
from datetime import datetime, timedelta
from bs4 import BeautifulSoup as bs
from collections import OrderedDict
from threading import Thread, Lock
from dataclasses import dataclass
from statistics import mean
from string import Template
from winsound import Beep
from inspect import trace
from pprint import pprint
import os
from os import system
import numpy as np
import requests
import string
import json
import time
import math
import ssl
import sys

from subprocess import call, DEVNULL

from functions import *