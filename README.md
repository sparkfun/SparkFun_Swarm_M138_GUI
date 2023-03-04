SparkFun Sawrm M138 GUI
========================================

![Swarm M138 GUI](images/GUI_1.png)

The Swarm M138 GUI is a simple, easy to use GUI for the Swarm M138 satellite modem. Available on all major platforms, as well as a Python package, the GUI will get you up and running with Swarm satellite communication. 

If you need to install the application, see the [Installation Section](#installation) of this page.


# Using the GUI
  
Click any of the pre-defined message buttons to send that message to the modem. Or enter your own message in the Message window and click Send Message to send it. The $, * and checksum are added automatically. You do not need to include those.

## Installation

Installation binaries are available for all major platforms (macOS, Window, and Linux) on the release page of the GUI repository:

[**Swarm M138 GUI Release Page**](https://github.com/sparkfun/SparkFun_Swarm_M138_GUI/releases)

Click the arrow next to **Assets** if required to see the installers:

![Releases Assets](images/Assets.png)


### Windows
* Download the github release zip file - *.win.zip.zip*
* Unzip the release file - *.zip*
* This results in the application executable, *.exe*
* Double-click *.exe* to start the application

### macOS
* Download the release file - *.dmg.zip*
* Double click on the file to unzip the file to *.dmg*
* Double click the *.dmg* file to mount the disk image. 
* A Finder window, with the contents of the file will open
* Install the *.app* by dragging it on the *Applications* in the Finder Window, or copying the file to a desired location.
* Once complete, unmount the disk image by right-clicking on the mounted disk in Finder and ejecting it.
* You may need to install drivers for the CH340 USB interface chip. Full instructions can be found in our [CH340 Tutorial](https://learn.sparkfun.com/tutorials/how-to-install-ch340-drivers/all#mac-osx)

To launch the GUI:
* Double-click .app to launch the application
* The .app isn't signed, so macOS won't run the application, and will display a warning dialog. Dismiss this dialog.
* To approve app execution bring up the macOS *System Preferences* and navigate to: *Security & Privacy > General*. 
* On this page, select the *Open Anyway* button to launch the application.
* Once selected, macOS will present one last dialog. Select *Open* to run the application. The GUI will now start.

### Linux
* Download the github release zip file - *.linux.gz.zip*
* Unzip the release file - *.linux.gz*
* Un-gzip the file, either by double-clicking in on the desktop, or using the `gunzip` command in a terminal window. This results in the file ** 
* To run the application, the file must have *execute* permission. This is performed by selecting *Properties* from the file right-click menu, and then selecting permissions. You can also change permissions using the `chmod` command in a terminal window.
* Once the application has execute permission, you can start the application a terminal window. Change directory's to the application location and issue `./`
* You may need to install drivers for the CH340 USB interface chip. Full instructions can be found in our [CH340 Tutorial](https://learn.sparkfun.com/tutorials/how-to-install-ch340-drivers/all#linux)


### Python Package
The GUI is also provided as an installable Python package. This is advantageous for platforms that lack a pre-compiled application. 

To install the Python package:
* Download the package file - *python-install-package.zip*
* Unzip the github release file. This results in the installable Python package file - *.tar.gz* (note - the version number might vary)

At a command line - issue the package install command:

* `pip install .tar.gz`
* Once installed, you can start the GUI by issuing the command `./Swarm_M138` at the command line. (To see the command, you might need to start a new terminal, or issue a command like `rehash` depending on your platform/shell)

Notes:
* A path might be needed to specify the install file location.
* Depending on your platform, this command might need to be run as admin/root.
* Depending on your system, you might need to use the command `pip3`

### Raspberry Pi
We've tested the GUI on 64-bit Raspberry Pi Debian. You will need to use the **Python Package** to install it.

Notes:
* On 32-bit Raspberry Pi, with both Python 2 and Python 3 installed, use `sudo pip3 install .tar.gz`
  * By default, the executable will be placed in `/usr/local/bin`
* On 64-bit Raspberry Pi, use `sudo pip install .tar.gz`
* The `sudo` is required to let `setup.py` install `python3-pyqt5` and `python3-pyqt5.qtserialport` using `sudo apt-get install`
