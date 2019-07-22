from configuration import config


def get_html_form():
    if config["PM1"]:
        PM1_state = "checked"
    else:
        PM1_state = ""
    if config["PM2"]:
        PM2_state = "checked"
    else:
        PM2_state = ""
    if config["TEMP"]:
        TEMP_state = "checked"
    else:
        TEMP_state = ""
    if config["GPS"]:
        GPS_state = "checked"
    else:
        GPS_state = ""

    is_selected = {"Critical":"", "Error":"", "Warning":"", "Info":"", "Debug":""}
    for level in is_selected:
        if level == config["logging_lvl"]:
            is_selected[level] = " selected"

    html_form = '''<!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            <title>Configuration</title>
            <style>
                body { background-color: #1a9edb;
                  font-family: 'Open Sans', sans-serif;
                  font-size: 18px;
                  margin: 20px 25px 70px 25px;}
                h1 { color: white; }
                .id_section {
                  float: left;
                  width: 280px;}
                .interval_section {
                  float: left;
                  width: 130px;}
                .config_form { color: white;}
                .config_form_input_text{
                  position: relative;
                  margin-bottom: 5px;
                  box-sizing: border-box;
                  padding: 4px;
                  width: 240px;
                  height: 23px;}
                .config_form_input_number{
                  position: relative;
                  margin-bottom: 5px;
                  box-sizing: border-box;
                  padding: 4px;
                  width: 75px;
                  height: 23px;}
                .config_form_label{
                  display: block;
                  font-size: 75%;}
                .config_form_label_checkbox{
                  display: inline;
                  font-size: 85%;
                  vertical-align: 30%;}
                .config_form_input_checkbox{
                  width: 20px;
                  height: 20px;}
                .config_form_input_select{
                  width: 130px;
                  height: 25px;}
                .config_form_button{
                  width: 130px;
                  height: 35px;}
            </style>
        </head>
        <body>
              <h1 class="heading">PM Sensor Configuration</h1>
              <form class="config_form">
                <p class="heading">General Settings:</p>
                <label class="config_form_label">Device ID: ''' + str(config["device_id"]) + '''</label>
                <br>
                <label class="config_form_label" for="device_name">Device Name</label>
                <input class="config_form_input_text" id="device_name" name="device_name" type="text" value="''' + str(config["device_name"]) + '''" required="required" maxlength="32"/>
                <label class="config_form_label" for="password">New Password</label>
                <input class="config_form_input_text" id="password" name="password" type="password" value="''' + str(config["password"]) + '''" required="required" maxlength="32"/>
                <p class="heading">LoRaWAN Configuration:</p>
                <label class="config_form_label">Device EUI: ''' + str(config["device_eui"]) + '''</label>
                <br>
                <label class="config_form_label" for="region">Region</label>
                <input class="config_form_input_text" id="region" name="region" type="text" value="''' + str(config["region"]) + '''" required="required" maxlength="32"/>
                <label class="config_form_label" for="application_eui">Application EUI</label>
                <input class="config_form_input_text" id="application_eui" name="application_eui" type="text" value="''' + str(config["application_eui"]) + '''" required="required" maxlength="16"/>
                <label class="config_form_label" for="app_key">App Key</label>
                <input class="config_form_input_text" id="app_key" name="app_key" type="password" value="''' + str(config["app_key"]) + '''" required="required" maxlength="32"/>
                <p class="heading">MQTT Configuration:</p>
                <label class="config_form_label" for="application_id">Application ID</label>
                <input class="config_form_input_text" id="application_id" name="application_id" type="text" value="''' + str(config["application_id"]) + '''" required="required" maxlength="32"/>
                <label class="config_form_label" for="access_key">Access Key</label>
                <input class="config_form_input_text" id="access_key" name="access_key" type="password" value="''' + str(config["access_key"]) + '''" required="required" maxlength="128"/>
                <label class="config_form_label" for="raw_interval">Raw Data Interval (hours)</label>
                <input class="config_form_input_text" id="raw_interval" name="raw_interval" type="number" value="''' + str(config["raw_interval"]) + '''" required="required" min="0.1" max="8760" step="0.01"/>
                <p class="heading">Preferences:</p>
                <input class="config_form_input_checkbox" id="PM1" name="PM1" type="checkbox" value="True" ''' + PM1_state + '''/>
                <label class="config_form_label_checkbox" for="PM1">PM Sensor 1</label>
                <input class="config_form_input_checkbox" id="PM2" name="PM2" type="checkbox" value="True" ''' + PM2_state + '''/>
                <label class="config_form_label_checkbox" for="PM2">PM Sensor 2</label>
                <input class="config_form_input_checkbox" id="TEMP" name="TEMP" type="checkbox" value="True" ''' + TEMP_state + '''/>
                <label class="config_form_label_checkbox" for="TEMP">Temperature &amp; Humidity</label>
                <input class="config_form_input_checkbox" id="GPS" name="GPS" type="checkbox" value="True" ''' + GPS_state + '''/>
                <label class="config_form_label_checkbox" for="GPS">GPS</label>
                <br><br>
                <div class="id_section">
                <label class="config_form_label" for="PM1_id">PM1 Sensor ID</label>
                <input class="config_form_input_number" id="PM1_id" name="PM1_id" type="number" value="''' + str(config["PM1_id"]) + '''" required="required" min="0" max="65535"/>
                <label class="config_form_label" for="PM2_id">PM2 Sensor ID</label>
                <input class="config_form_input_number" id="PM2_id" name="PM2_id" type="number" value="''' + str(config["PM2_id"]) + '''" required="required" min="0" max="65535"/>
                <label class="config_form_label" for="TEMP_id">Temp &amp; Humidity Sensor ID</label>
                <input class="config_form_input_number" id="TEMP_id" name="TEMP_id" type="number" value="''' + str(config["TEMP_id"]) + '''" required="required" min="0" max="65535"/>
                <label class="config_form_label" for="GPS_id">GPS Sensor ID</label>
                <input class="config_form_input_number" id="GPS_id" name="GPS_id" type="number" value="''' + str(config["GPS_id"]) + '''" required="required" min="0" max="65535"/>
                </div>
                <div class="interval_section">
                <label class="config_form_label" for="PM1_interval">Interval (m)</label>
                <input class="config_form_input_number" id="PM1_interval" name="PM1_interval" type="number" value="''' + str(config["PM1_interval"]) + '''" required="required" min="1" max="120" step="0.01"/>
                <label class="config_form_label" for="PM2_interval">Interval (m)</label>
                <input class="config_form_input_number" id="PM2_interval" name="PM2_interval" type="number" value="''' + str(config["PM2_interval"]) + '''" required="required" min="1" max="120" step="0.01"/>
                <label class="config_form_label" for="TEMP_interval">Interval (m)</label>
                <input class="config_form_input_number" id="TEMP_interval" name="TEMP_interval" type="number" value="''' + str(config["TEMP_interval"]) + '''" required="required" min="1" max="120" step="0.01"/>
                <label class="config_form_label" for="GPS_interval">Interval (h)</label>
                <input class="config_form_input_number" id="GPS_interval" name="GPS_interval" type="number" value="''' + str(config["GPS_interval"]) + '''" required="required" min="0.1" max="8760" step="0.01"/>
                </div>
                <br><br>
                <label class="config_form_label" for="logging_lvl">Select Logging Level</label>
                <select class="config_form_input_select" id="logging_lvl" name="logging_lvl">
                  <option'''+str(is_selected["Critical"])+'''>Critical</option>
                  <option'''+str(is_selected["Error"])+'''>Error</option>
                  <option'''+str(is_selected["Warning"])+'''>Warning</option>
                  <option'''+str(is_selected["Info"])+'''>Info</option>
                  <option'''+str(is_selected["Debug"])+'''>Debug</option>
                </select>
                <br><br>
                <button class="config_form_button" type="submit">Save</button>
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

# html_acknowledgement = '''<!DOCTYPE html>
#             <html>
#                 <head>
#                     <title>Configuration</title>
#                 </head>
#                 <style>
#                     body {{ background-color: #18bcd9; }}
#                     h2 {{ color: white; }}
#                     p {{ color: white; }}
#                 </style>
#                 <body>
#                     <br>
#                     <h2>Sensor Configured as Follows:</h2>
#                     <p>LoRa Application Key:<br> {} <br>
#                     <br>
#                     LoRa Application EUI:<br> {} <br>
#                     <br>
#                     Data is sent every:<br> {} minutes
#                     </p>
#                 </body>
#             </html>'''
