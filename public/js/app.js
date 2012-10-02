$(document).ready(function () {
/**
 * The app object
 */ 
var App = {
  baseUrl: "/",
  apiUrl: "/api/"
};

/**
 * The api model
 */
App.ApiModel = Backbone.Model.extend({
  defaults:{
    api: '',
    platform: '',
    access_token: '',
    open_id: '',
    response: null
  },

  /**
   * Get the access token, will check the cookie first
   * redirect to authorization page if access token not in cookie
   *
   * @param String platform
   */
  getAccessToken: function (platform) {
    var old = $.cookie(platform + "_access_token");
    if (old) {
      var attributes = {
        platform: platform,
        access_token: old
      };
      if (platform == 'tencent') {
        attributes['open_id'] = $.cookie('tencent_open_id');
      } 

      this.set(attributes);
    } else {
      $.ajax({
        url: App.apiUrl + "getAuthorizationUrl?platform=" + platform,
        dataType: 'json',
        success: function (resp) {
          if (resp.code == 0) {
            window.location.href = resp.data;
          } else {
            alert('Error: ' + resp.message);
          }
        }
      });
    }
  },

  /**
   * Set the access token
   */
  setAccessToken: function (platform, access_token) {
    this.set({'platform': platform, 'access_token': access_token});
  },

  /**
   * Call the api
   */
  callApi: function () {
    var data = this.toJSON();
    delete data['response'];
    if (this.get('platform') != 'tencent') {
      delete data['open_id'];
    }

    $.ajax({
      url: App.apiUrl + 'api',
      dataType: 'text',
      data: data,
      context: this,
      success: function (rep) {
        this.set({'response': rep});
      }
    });
  },

  /**
   * Detect the query string in the url
   * fetch the access token if code is in the url
   * and save the access token in the cookie
   */
  autoDetectAuthorizationCode: function () {
    var search = window.location.search;
    var re = /(?:\?|&(?:amp;)?)([^=&#]+)(?:=?([^&#]*))/g,
        match, params = {},
        decode = function (s) {return decodeURIComponent(s.replace(/\+/g, " "));};

    while (match = re.exec(search)) {
      params[decode(match[1])] = decode(match[2]);
    }

    var code = params['code'] || '';
    if (code) {
      var platform = params['state'] || 'tencent';
      $.ajax({
        url: App.apiUrl + "getAccessToken?code=" + code + "&platform=" + platform,
        dataType: 'json',
        context: this,
        success: function (resp) {
          if (resp.code == 0) {
            var open_id = params['openid'] || '';
            this.set({open_id: open_id}, {silent: true});
            this.setAccessToken(platform, resp.data);

            // save access token to cookie
            $.cookie(platform + "_access_token", resp.data);
            if (platform == 'tencent') {
              $.cookie("tencent_open_id", open_id);
            }
          } else {
            alert('Error: ' + resp.message);
          }
        }
      });
    }
  }
});

/**
 * The form view
 */
App.FormView = Backbone.View.extend({
  _tplParameterItem: null,

  initialize: function () {
    this._tplParameterItem = _.template($("#tpl_parameter").html());
    this.model.on('change', this.render, this);
  },

  events: {
    "change #select_platform": "onSelectFormChange",
    "click #a_add_more": "addMoreParameter",
    "click .btn-primary": "callApi"
  },

  /**
   * Render function
   */
  render: function () {
    // platform
    this.$("#select_platform").val(this.model.get('platform'));

    // api
    this.$("#input_api").val(this.model.get('api'));

    // parameters
    var params = this.model.attributes;
    var reserved = params['platform'] == 'tencent'
                   ? ['platform', 'api', 'response']
                   : ['platform', 'api', 'response', 'open_id'];

    var i = 0;
    for (var k in params) {
      if (reserved.indexOf(k) >= 0) {
        continue;
      }
      i++;
    }

    var diff = $("#ul_parameter_list li").size() - i;
    while (diff < 0) {
      this.addMoreParameter();
      diff++;
    }

    $("#ul_parameter_list").find("input").val('');

    i = 0;
    for (k in params) {
      if (reserved.indexOf(k) >= 0) {
        continue;
      }

      var li = $("#ul_parameter_list li").eq(i);
      li.find("input.span2").val(k);
      li.find("input.span4").val(params[k]);

      i++;
    }

    // response
    if (this.model.get('response')) {
      this.$("#textarea_response").text(this.model.get('response'));
    }
  },

  onSelectFormChange: function (e) {
    var platform = $(e.target).val();
    this.model.getAccessToken(platform);
  },

  addMoreParameter: function () {
    var total = $("#ul_parameter_list li").size();
    $("#ul_parameter_list").append(this._tplParameterItem());
  },

  callApi: function (e) {
    var api = $.trim(this.$("#input_api").val());
    if (api == '') {
      e.preventDefault();
      return ;
    }

    var attributes = {
      platform: this.$("#select_platform").val(),
      api: api,
      response: ''
    };

    $("#ul_parameter_list li").each(function (idx, li) {
      li = $(li);
      var name = $.trim(li.find("input.span2").val());
      var value = $.trim(li.find("input.span4").val());
      if (name && value) {
        attributes[name] = value;
      }
    });

    this.model.set(attributes, {silent: true});
    this.model.callApi();

    e.preventDefault();
    return false;
  }
});

// setup cookie plugin
$.cookie.defaults = {
  expires: new Date((+new Date()) + 3600000), // 1 hour
  path: '/'
}

var api = new App.ApiModel();
var form = new App.FormView({el: $('#form_settings'), model: api});
api.autoDetectAuthorizationCode();
});
