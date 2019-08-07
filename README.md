# Plantower Particulate Sensor Python interface for Pycom boards
A basic python interface for interacting with the plantower PM sensors.  This code has been tested with the following devices:
 * Plantower PMS5003
 * Plantower PMS7003
 * Plantower PMSA003
 
 It may work with other sensors from the plantower range, if you try it please do let us know either way.  If there are any problems with it please either raise an issue or fix it and issue a pull request.
 
 ## Usage
The quickest and easiest way is to download the whole plantawerpycom repository and place it inside your project's lib folder. Example of usage is shown in `example/main.py`. To run this example, place the `example/main.py` inside your project directory, so that the project structure is as follows:
<pre>
Your-project-folder
|-lib
  |-plantowerpycom
    |-__init__.py
    |-logging.py
    |-plantower.py
|-main.py
</pre>
Then you can upload your project to the board (e.g. using Pymark). The example code assumes that the Plantower sensor is connected to pins P10 and P11 of LoPy board.

Alternative is to clone the repository using subtree. In your main project directory (that is a git repo), run 
```bash
git subtree add --prefix lib/plantowerpycom https://github.com/FEEprojects/plantowerpycom.git master --squash
```
which clones the plantowerpycom repository as a subtree inside the lib directory of your project.
To pull from the original plantowerpycom repository, run
```bash
git subtree pull --prefix lib/plantowerpycom https://github.com/FEEprojects/plantowerpycom.git master --squash
```