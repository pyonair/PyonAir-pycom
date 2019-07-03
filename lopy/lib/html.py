html_form = '''<!DOCTYPE html>
            <html>
                <head>
                    <title>Configuration</title>
                </head>
                <style>
                    body { background-color: #18bcd9; }
                    h1 { color: white; }
                    h2 { color: white; }
                    form { color: white; }
                </style>
                <body>
                    <h1>PM Sensor Configuration</h1>
                    <br>
                    <h2>Enter Credentials and Preferences:</h2>
                    <p>
                    <form action="" method="post">
                            LoRa Application Key:<br>
                            <input type="text" name="APP_KEY" size="50" required>
                            <br><br>
                            LoRa Application EUI:<br>
                            <input type="text" name="APP_EUI" size="50" required>
                            <br><br>
                            Sensor Average Interval (min):<br>
                            <input type="text" name="interval" size="50" required>
                            <br><br>
                            <input type="submit" value="Send">
                    </form></p>
                </body>
            </html>'''

html_acknowledgement = '''<!DOCTYPE html>
            <html>
                <head>
                    <title>Configuration</title>
                </head>
                <style>
                    body {{ background-color: #18bcd9; }}
                    h2 {{ color: white; }}
                    p {{ color: white; }}
                </style>
                <body>
                    <br>
                    <h2>Sensor Configured as Follows:</h2>
                    <p>LoRa Application Key:<br> {} <br>
                    <br>
                    LoRa Application EUI:<br> {} <br>
                    <br>
                    Data is sent every:<br> {} minutes
                    </p>
                </body>
            </html>'''