#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
from handlers.SiteHandler import SiteHandler
from handlers.ApiHandler import ApiHandler

routes = [webapp2.Route(r'/', handler=SiteHandler, name='site'),
          webapp2.Route(r'/api/<action:[a-zA-Z0-9_-]+>', handler=ApiHandler, name='api')]

app = webapp2.WSGIApplication(routes, debug=True)
