#####
## Author: Alan M
#####
# ------------------------------
# IMPORT STATEMENTS
# ------------------------------
import sys, traceback, os
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QCheckBox, QPushButton, QRadioButton,QHBoxLayout, QVBoxLayout, QGridLayout, QFontDialog, QFileDialog, QComboBox, QMdiArea, QMdiSubWindow, QTextEdit
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot, QTimer, QThreadPool, QDir
import matplotlib, math
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT  as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np
from numpy import *
import h5py
import time
#import MatlabCode 

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # # Add the callback to our kwargs
        # kwargs['progress_callback'] = self.signals.progress
    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


# Main Class
class Data_GUI(QMainWindow):
	def __init__(self, DAQ=0,*args, **kwargs):
		super(Data_GUI,self).__init__(*args, **kwargs)
		self.setWindowTitle('SNP Data')
		self.create_main_frame()
		self.create_status_bar()


		#Default settings
		self.sample_rate = 8e5
		self.stop_loop = False
		self.number_channels = 1
		self.counter = 0

		# Event connections/signals
		self.take_sweep_button.pressed.connect(self.do_sweep_worker)
		self.take_noise_bx.pressed.connect(self.take_noise_worker)
		self.take_pulses_bx.pressed.connect(self.take_pulses_worker)
		self.browse_button.pressed.connect(self.browse_clicked)

		self.popup_noise.pressed.connect(self.noise_graph_clicked)

		self.system.activated[str].connect(self.system_pref)

		#Thread Initialization
		self.threadpool = QThreadPool()
	def do_stop_data(self):
		self.stop_loop = 1
	def create_status_bar(self):
		self.status_text = QLabel("Status: Awaiting orders.")
		self.statusBar().addWidget(self.status_text, 1)
	def create_main_frame(self):
		""" Creates Main Frame. Adds boxes and labels  """
		self.main_frame = QWidget()

		#Labels and Default Settings
		self.data_path_label= QLabel('Data Path:')
		self.data_path_txtbx= QLineEdit('/Users/alanmc/Documents')
		self.browse_button= QPushButton('Browse')
		self.selec_sys = QLabel('Select System:')
		self.system = QComboBox(self)
		self.system.addItem('Sys 1')
		self.system.addItem('Cheap Sys')

		self.start_temp_label = QLabel('Start Temp (mK)')
		self.start_temp_txtbx = QLineEdit('80')
		self.stop_temp_label = QLabel('Stop Temp (mk)')
		self.stop_temp_txtbx = QLineEdit('2')
		self.temp_step_label= QLabel('Temp Step (mK)')
		self.stop_temp_txtbx = QLineEdit('10')
		self.wait_time_label= QLabel('Wait Time (s)')
		self.wait_time_txtbx = QLineEdit('0')

		self.start_atten_label= QLabel('Start Atten (dB)')
		self.start_atten_txtbx = QLineEdit('25')
		self.stop_atten_label= QLabel('Stop Atten (dB)')
		self.stop_atten_txtbx = QLineEdit('25')
		self.atten_step_label = QLabel('Atten Step (dB)')
		self.atten_step_txtbx = QLineEdit('25')
		self.tot_atten_label= QLabel('Tot Atten (dB)')
		self.tot_atten_txtbx = QLineEdit('25')

		self.numb_res_label= QLabel('Resonators')
		self.num_res_1_bx= QRadioButton('1 Res')
		self.num_res_2_bx= QRadioButton('2 Res')
		self.numb_freq_steps_label= QLabel('Number of Freq Steps')
		self.numb_freq_steps_txtbx= QLineEdit('1000')
		self.sample_avg_label= QLabel('Samples to Average')
		self.sample_avg_txtbx = QLineEdit('10000')
		self.sweep_sampling_rate_label= QLabel('Sweep Sampling Rate (Hz)')
		self.sweep_sampling_rate_txtbx = QLineEdit('8e4')
		self.used_fixed_span_bx = QCheckBox('Used Fixed Span')



		#Sweep Settings
		self.take_sweep_button = QPushButton('Do Sweep')
		self.res_graph_label= QLabel('Resonator Graph')

		#Noise Settings
		self.take_noise_bx = QPushButton('Take Noise')
		self.time_per_integration_label= QLabel('Time Per\nIntegration (s)')
		self.time_per_integration_txtbx= QLineEdit('1')
		self.total_time_label= QLabel('Total Time (s)')
		self.total_time_txtbx= QLineEdit('10')
		self.noise_sampling_rate_label= QLabel('Noise Sampling\nRate (Hz)')
		self.noise_sampling_rate_txtbx= QLineEdit('8e4')
		self.decimation_factor_label= QLabel('Decimation Factor')
		self.decimation_factor_txtbx= QLineEdit('4')
		self.take_add= QCheckBox('Take Additional')
		self.take_add_txtbx= QLineEdit('7')
		self.take_add_label= QLabel('points at')
		self.take_add2_txtbx= QLineEdit('10')
		self.take_add2_label= QLabel('kHz Spacing')
		self.use_100khz_fit= QCheckBox('Use 1000kHz AA Fit')
		self.save_raw_data= QCheckBox('Save Raw Data Every (mK)')
		self.save_raw_data_label= QLineEdit('30')
		self.calc_spectra= QCheckBox('Calculate Spectra')
		self.cpsd_btw_res= QCheckBox('CPSD Between Res')
		self.take_offres_data= QCheckBox('Take Offres Data')
		self.spectra_settings= QPushButton('Spectra Settings')
		self.fit_type_label= QLabel('Fit Type')
		self.quick_fit_bx= QRadioButton('Quick Fit')
		self.full_fit_bx= QRadioButton('Full Fit') 
		self.popup_noise = QPushButton('Open Noise Graph')

		#Pulse Settings
		self.take_pulses_bx = QPushButton('Take Pulses')
		self.pulses_graph_labeled = QLabel('Pulses Graph')
		#-----------------------------------------------------------------------
		# Widget Lists (order matters) 
		settings_w_lst = [ self.data_path_label, self.data_path_txtbx, self.browse_button, self.selec_sys, self.system, self.start_temp_label, self.start_temp_txtbx, self.stop_temp_label, self.stop_temp_txtbx, self.wait_time_label, self.wait_time_txtbx,
		self.start_atten_label, self.start_atten_txtbx, self.stop_atten_label, self.stop_atten_txtbx, self.atten_step_label, self.atten_step_txtbx, self.tot_atten_label, self.tot_atten_txtbx,
		self.numb_res_label, self.num_res_1_bx, self.num_res_2_bx, self.numb_freq_steps_label, self.numb_freq_steps_txtbx, self.sample_avg_label, self.sample_avg_txtbx, self.sweep_sampling_rate_label, self.sweep_sampling_rate_txtbx, self.used_fixed_span_bx]
		
		sweep_settings_w_lst=[self.take_sweep_button, self.res_graph_label]

		noise_settings_w_lst=[self.take_noise_bx, self.time_per_integration_label, self.time_per_integration_txtbx, self.total_time_label, self.total_time_txtbx, 
		self.noise_sampling_rate_label,self.noise_sampling_rate_txtbx, self.decimation_factor_label, self.decimation_factor_txtbx, self.take_add, self.take_add_txtbx, self.take_add_label, self.take_add2_txtbx, self.take_add2_label,
		self.use_100khz_fit, self.save_raw_data, self.save_raw_data_label, self.calc_spectra, self.cpsd_btw_res, self.take_offres_data, self.spectra_settings, self.fit_type_label, self.quick_fit_bx, self.full_fit_bx, self.popup_noise]

		pulse_settings_w_lst=[self.take_pulses_bx,self.pulses_graph_labeled]
		#-----------------------------------------------------------------------
		
		# Creates layout
		grid = QGridLayout()
		grid.setSpacing(5)
		for i in range(len(settings_w_lst)):
			w = settings_w_lst[i]
			w.setMaximumWidth(200)
			grid.addWidget(w,i,0)

		for i in range(len(sweep_settings_w_lst)):
			w = sweep_settings_w_lst[i]
			w.setMaximumWidth(200)
			grid.addWidget(w,i,1)

		for i in range(len(noise_settings_w_lst)):
			w = noise_settings_w_lst[i]
			w.setMaximumWidth(200)
			grid.addWidget(w,i,2)

		for i in range(len(pulse_settings_w_lst)):
			w = pulse_settings_w_lst[i]
			w.setMaximumWidth(200)
			grid.addWidget(w,i,3)

		self.main_frame.setLayout(grid)
		self.setCentralWidget(self.main_frame)

	#Functions for Launch
	def browse_clicked(self):
		"""If Browse button clicked a dialog box will open to select new directory """
		options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
		directory = QFileDialog.getExistingDirectory(self,"QFileDialog.getExistingDirectory()",
			self.data_path_txtbx.text(), options=options)
		self.data_path_txtbx.setText(directory)
	def system_pref(self):
		pass
	def do_sweep_clicked(self):
		t = time.time()
		time.sleep(5)
		self.take_sweep_button.setText('Doing Sweep')
		self.status_text.setText('Status: Doing Sweep')
		time.sleep(5)
		#MatlabCode.printing()
		print("sweep is done in : ",time.time()-t)
		self.status_text.setText('Status: Sweep Done')
		time.sleep(3)
		self.take_sweep_button.setText('Do Sweep')

	def take_noise_clicked(self):
		t = time.time()
		time.sleep(5)
		self.take_noise_bx.setText('Taking Noise')
		self.status_text.setText('Status: Taking Noise')
		time.sleep(3)
		print("noise is done in : ",time.time()-t)
		self.status_text.setText('Status: Noise Done')
		time.sleep(3)
		#MatlabCode.printing()
		self.take_noise_bx.setText('Take Noise')
	def take_pulses_clicked(self):
		t = time.time()
		time.sleep(5)
		self.take_pulses_bx.setText('Taking Pulses')
		self.status_text.setText('Status: Taking Pulses')
		time.sleep(3)
		#MatlabCode.printing()
		print("Pulses are done in : ",time.time()-t)
		self.status_text.setText('Status: Pulses Done')
		time.sleep(3)
		self.take_pulses_bx.setText('Take Pulses')

	def noise_graph_clicked(self):
		sub = QMdiSubWindow()
		sub.setWidget(QTextEdit())
		sub.setWindowTitle("Noise Graph")
		self.mdi.addSubWindow(sub)
		sub.show()



		# Workers
	def do_sweep_worker(self):
		worker = Worker(self.do_sweep_clicked)
		self.threadpool.start(worker)
	def take_noise_worker(self):
		worker = Worker(self.take_noise_clicked)
		self.threadpool.start(worker)
	def take_pulses_worker(self):
		worker = Worker(self.take_pulses_clicked)
		self.threadpool.start(worker)



#Graph CLasses

# ------------------------------
# RUN EVENT LOOP UNTIL QUIT
# ------------------------------
def main():
	
	app = QApplication(sys.argv)
	form = Data_GUI()
	form.setGeometry(100,100,1000,600)
	form.show()
	app.exec_()
	
if __name__ == '__main__':
	main()