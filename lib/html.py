from Configuration import config


def get_html_form():

    is_selected = {"Critical":"", "Error":"", "Warning":"", "Info":"", "Debug":""}
    for level in is_selected:
        if level == config.get_config("logging_lvl"):
            is_selected[level] = " selected"

    html_form = '''<!DOCTYPE html>
    <html>
      <head>
      <title>PyonAir Configuration</title>
      <style>
        
      body{
          background-color: #252525;
          margin-left: 25px;
          margin-top: 30px;
          margin-bottom: 45px;
          font-family: helvetica;
          color: white;
          font-size: 15px;}
    
        h1{
          margin-bottom: 0px;
        }
          
        p{
          font-size: 20px;
          margin-left: 5px;
          margin-bottom: 0px;
          margin-top: 2em;
        }
    
        hr {
            display: block;
            height: 1px;
            width: 270px;
            border: 0;
            border-top: 1px solid #909090;
            margin-top: 0.1em;
            margin-left: -5px;
        }
    
        .p_line{
          padding-bottom: 0.8em;
        }
    
        form {
          margin-left: 5px;
        }
    
        label {
          display: block;
          margin-top: 1em;
        }
    
        .settings{
          margin-left: 30px;
        }
    
        .settings hr{
          width: 380px;
        }
    
        .pm_sensors{
          margin-left: 15px;
          display: grid;
          grid-template-columns: 260px 110px;
        }
    
        .pm_sensors .pm_sensor_label{
          margin-top: 1em;
        }
    
        .pm_sensors hr{
          width: 230px;
        }
    
        input{
          margin-top: 5px;
          box-sizing: border-box;
          height: 1.8em;
          padding: 2px 4px;
          width: 200px;
        }
    
        select{
          margin-top: 5px;
          width: 110px;
          height: 1.8em;
        }
    
        .sensor{
          display: grid;
          grid-template-columns: 150px 110px 110px;
          margin-left: 10px;
          margin-top: -0.5em;
          margin-bottom: 1.8em;
        }
    
        .input_number{
          width: 70px;
        }
    
        .pm_sensors .sensor{
            grid-template-columns: 150px 110px;
            margin-left: -5px;
            margin-bottom: 0;
            margin-top: -1.3em;
        }
    
        .grid_item3{
          grid-column-start: 2;
          grid-column-end: 3;
          grid-row-start: 1;
          grid-row-end: 4;
          margin-top: 50%;
          margin-left: -5px;
        }
    
        .sensor_settings{
          width: 450px;
        }
      </style>
      </head>
      <body>
        <form class="config_form">
          <h1>PyonAir Configuration</h1>
          <p>General Settings</p>
          <hr class="p_line"/>
          <div class="settings">
            <label>Unique ID: ''' + str(config.get_config("device_id")) + '''</label>
            <label for="device_name">Device Name</label>
            <input id="device_name" name="device_name" type="text" value="''' + str(config.get_config("device_name")) + '''" required="required" maxlength="32"/>
            <label for="password">New Password</label>
            <input id="password" name="password" type="password" value="''' + str(config.get_config("password")) + '''" required="required" maxlength="32"/>
          </div>
          <p>LoRaWAN Configuration</p>
          <hr class="p_line"/>
          <div class="settings">
            <label>Device EUI: ''' + str(config.get_config("device_eui")) + '''</label>
            <label for="application_eui">Application EUI</label>
            <input id="application_eui" name="application_eui" type="text" value="''' + str(config.get_config("application_eui")) + '''" required="required" maxlength="16"/>
            <label for="app_key">App Key </label>
            <input id="app_key" name="app_key" type="password" value="''' + str(config.get_config("app_key")) + '''" required="required" maxlength="32"/>
            <label for="region">Region</label>
            <select name="region">
              <option>Europe</option>
              <option>Asia</option>
              <option>Australia</option>
              <option>United States</option>
            </select>
          </div>
          <p>MQTT Configuration - Not implemented</p>
          <hr class="p_line"/>
          <div class="settings">
            <label for="SSID">SSID</label>
            <input id="SSID" name="SSID" type="text" value="''' + str(config.get_config("SSID")) + '''" required="required" maxlength="32"/>
            <label for="wifi_password">Password</label>
            <input id="wifi_password" name="wifi_password" type="password" value="''' + str(config.get_config("wifi_password")) + '''" required="required" maxlength="128"/>
            <label for="raw_freq">Raw data back-up frequency</label>
            <input id="raw_freq" name="raw_freq" type="number" value="''' + str(config.get_config("raw_freq")) + '''" required="required" min="0.1" max="8760" step="0.01"/>
          </div>
          <p>Sensor Settings</p>
          <hr class="p_line sensor_settings"/>
          <div class="settings">
            <label>Temperature and Humidity Sensor</label>
            <hr/>
            <div class="sensor">
              <div>
                <label for="TEMP_type">Sensor Type</label>
                <select name="TEMP_type">
                  <option>SHT35</option>
                </select>
              </div>
              <div>
                <label for="TEMP_id">Sensor ID</label>
                <input class="input_number" id="TEMP_id" name="TEMP_id" type="number" value="''' + str(config.get_config("TEMP_id")) + '''" required="required" min="0" max="65535"/>
              </div>
              <div>
                <label for="TEMP_freq">Frequency</label>
                <input class="input_number" id="TEMP_freq" name="TEMP_freq" type="number" value="''' + str(config.get_config("TEMP_freq")) + '''" required="required" min="1" max="120" step="0.01"/>
              </div>
            </div>
            <label>Particulate Matter Sensors</label>
            <hr/>
            <div class="pm_sensors">
                <div class="grid_item1">
                  <label class="pm_sensor_label">PM Sensor 1</label>
                  <hr/>
                </div>
                <div class="sensor grid_item2">
                  <div>
                    <label for="PM1_type">Sensor Type</label>
                    <select name="PM1_type">
                      <option>PMS5003</option>
                      <option>SPS030</option>
                      <option>NONE</option>
                    </select>
                  </div>
                  <div>
                    <label for="PM1_id">Sensor ID</label>
                    <input class="input_number" id="PM1_id" name="PM1_id" type="number" value="''' + str(config.get_config("PM1_id")) + '''" required="required" min="0" max="65535"/>
                  </div>
                </div>
                <div class="grid_item3">
                  <label for="PM_interval">Interval</label>
                  <input class="input_number" id="PM_interval" name="PM_interval" type="number" value="''' + str(config.get_config("PM_interval")) + '''" required="required" min="1" max="120" step="0.01"/>
                </div>
                <div class="grid_item4">
                  <label class="pm_sensor_label">PM Sensor 2</label>
                  <hr/>
                </div>
                <div class="sensor grid_item5">
                  <div>
                    <label for="PM2_type">Sensor Type</label>
                    <select name="PM2_type">
                      <option>PMS5003</option>
                      <option>SPS030</option>
                      <option>NONE</option>
                    </select>
                  </div>
                  <div>
                    <label for="PM2_id">Sensor ID</label>
                    <input class="input_number" id="PM2_id" name="PM2_id" type="number" value="''' + str(config.get_config("PM2_id")) + '''" required="required" min="0" max="65535"/>
                  </div>
                </div>
              </div>
            <label>GPS - Not implemented</label>
            <hr/>
            <div class="sensor">
              <div>
                <label for="GPS">State</label>
                <select name="GPS">
                  <option>ON</option>
                  <option>OFF</option>
                </select>
              </div>
              <div>
                <label for="GPS_id">Sensor ID</label>
                <input class="input_number" id="GPS_id" name="GPS_id" type="number" value="''' + str(config.get_config("GPS_id")) + '''" required="required" min="0" max="65535"/>
              </div>
              <div>
                <label for="GPS_freq">Frequency</label>
                <input class="input_number" id="GPS_freq" name="GPS_freq" type="number" value="''' + str(config.get_config("GPS_freq")) + '''" required="required" min="0.1" max="8760" step="0.01"/>
              </div>
            </div>
            <hr class="p_line sensor_settings"/>
            <label for="logging_lvl">Select Logging Level</label>
            <select id="logging_lvl" name="logging_lvl">
              <option'''+str(is_selected["Critical"])+'''>Critical</option>
              <option'''+str(is_selected["Error"])+'''>Error</option>
              <option'''+str(is_selected["Warning"])+'''>Warning</option>
              <option'''+str(is_selected["Info"])+'''>Info</option>
              <option'''+str(is_selected["Debug"])+'''>Debug</option>
            </select>
            <br><br>
            <button type="submit">Save</button>
        </form>
      </body>
      <script>
    
        const isValidElement = element => {
          return element.name && element.value;
        };
    
        const isValidValue = element => {
          return (!['checkbox'].includes(element.type) || element.checked);
        };
    
        const formToJSON = elements => [].reduce.call(elements, (data, element) => {
    
          // Make sure the element has the required properties and should be added.
          if (isValidElement(element) && isValidValue(element)) {
              data[element.name] = element.value;
          }
          return data;
        }, {});
    
        const handleFormSubmit = event => {
    
          // Stop the form from submitting since we’re handling that with AJAX.
          event.preventDefault();
    
          // Call our function to get the form data.
          const data = formToJSON(form.elements);
    
          // Use `JSON.stringify()` to make the output valid, human-readable JSON.
          var json_data = "json_str_begin" + JSON.stringify(data, null, "") + "json_str_end";
    
          json_data.replace(/\\n/g, '');
    
          var date = new Date();
          var now = 'time_begin'+date.getFullYear()+':'+(date.getMonth()+1)+':'+date.getDate()+':'+date.getHours()+":"+date.getMinutes()+":"+date.getSeconds()+'time_end';
    
          // ...this is where we’d actually do something with the form data...
          var xhttp = new XMLHttpRequest();
          xhttp.open("POST", "", true);
          xhttp.send(json_data+now);
        };
    
        const form = document.getElementsByClassName('config_form')[0];
        form.addEventListener('submit', handleFormSubmit);
    </script>
    </html>'''

    return html_form
