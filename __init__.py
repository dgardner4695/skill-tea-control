# TODO: Add an appropriate license to your skill before publishing.  See
# the LICENSE file for more information.

# Below is the list of outside modules you'll be using in your skill.
# They might be built-in to Python, from mycroft-core or from external
# libraries.  If you use an external library, be sure to include it
# in the requirements.txt file so the library is installed properly
# when the skill gets installed later by a user.

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
import serial
import inflect
import time

# Each skill is contained within its own class, which inherits base methods
# from the MycroftSkill class.  You extend this class as shown below.

# TODO: Change "Template" to a unique name for your skill
class TeaControlSkill(MycroftSkill):

    # The constructor of the skill, which calls MycroftSkill's constructor
    def __init__(self):
        super(TeaControlSkill, self).__init__(name="TeaControlSkill")
        
        # Initialize working variables used within the skill.
        self.CE_status = -1
        self.ser = serial.Serial('/dev/serial0', baudrate=115200, dsrdtr=False, timeout=0.25)
        self.gas_level = 0
        self.rpm = 0
        self.inf = inflect.engine()

    @intent_handler(IntentBuilder("").require("CheckEngine"))
    def handle_check_eng_intent(self, message):

        #self.ser = serial.Serial('/dev/serial0', baudrate=115200, dsrdtr=False, timeout=0.25)
        self.ser.reset_input_buffer()
        self.ser.write(b'checkengine_status\n')

        stat = self.ser.read(1)

        if stat.decode('utf-8') is '1':
            self.CE_status = 'on'
        elif stat.decode('utf-8') is '0':
            self.CE_status = 'off'

        self.speak_dialog('ce.status', data={'status': self.CE_status})

        #self.ser.close()

    @intent_handler(IntentBuilder("").require("GasLevel"))
    def handle_gas_level_intent(self, message):

        #self.ser = serial.Serial('/dev/serial0', baudrate=115200, dsrdtr=False, timeout=0.25)
        self.ser.reset_input_buffer()
        self.ser.write(b'analogread A0\n')

        stat = self.ser.read(4)

        gas_int = int(stat.decode('utf-8').split()[0])
        self.gas_level = self.inf.number_to_words(round(100*(gas_int/1024)))

        self.speak_dialog('gas.level', data={'level': self.gas_level})

        #self.ser.close()

    @intent_handler(IntentBuilder("").require("RPMRead"))
    def handle_rpm_read_intent(self, message):

        #self.ser = serial.Serial('/dev/serial0', baudrate=115200, dsrdtr=False, timeout=0.25)
        
        self.ser.reset_input_buffer()
        self.ser.write(b'analogread A1\n')

        stat = self.ser.read(4)

        rpm_int = int(stat.decode('utf-8').split()[0])
        self.rpm = self.inf.number_to_words(rpm_int * 1000)

        self.speak_dialog('rpm.read', data={'measure': self.rpm})

        #self.ser.close()

    #def stop(self):
    #    if (self.ser.isOpen()):
    #        self.ser.close()
    #    return True

# The "create_skill()" method is used to create an instance of the skill.
# Note that it's outside the class itself.
def create_skill():
    return TeaControlSkill()
