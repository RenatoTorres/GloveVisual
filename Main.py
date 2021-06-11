from PyQt5 import QtGui   # (the example applies equally well to PySide)
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from pyqtgraph import GraphicsLayoutWidget, mkColor
from threading import Event
import pyqtgraph as pg
import GloveSocket as gs
import numpy as np
import base64

NUM_SENSORS = 5

class App(GraphicsLayoutWidget):
    # Signal to indicate new data acquisition
    # Note: signals need to be defined inside a QObject class/subclass
    data_acquired = pyqtSignal(np.ndarray)

    # Kill our data acquisition thread when shutting down
    def closeEvent(self, close_event):
        self.threadkill.set()

    def createWidgets(self):
        ## Always start by initializing Qt (only once per application)

        ## Define a top-level widget to hold everything
        self.w = QtGui.QWidget()

        ## Create some widgets to be placed inside
        self.btn0 = QtGui.QPushButton('Calibrate Zero [0%]')
        self.btn100 = QtGui.QPushButton('Calibrate Full [100%]')
        self.btnclr = QtGui.QPushButton('Clear Calibration')
        self.text = QtGui.QLineEdit('enter text')
        self.listw = QtGui.QListWidget()
        self.pic = QtGui.QLabel()

        self.file_logo = r'2000px-Logo_TU_Chemnitz.svg.png'

        self.pm = QtGui.QPixmap(self.file_logo)
        self.pm2 = self.pm.scaled(200,200, aspectRatioMode=1)
        self.pic.setPixmap( self.pm2 )

        self.btn0.clicked.connect(self.onClickBtn0)
        self.btn100.clicked.connect(self.onClickBtn100)
        self.btnclr.clicked.connect(self.onClickBtnClear)

    def createPlotWidgets(self):
        for i in range(0,NUM_SENSORS):
                self.plotGlove.append( pg.PlotWidget(background=pg.mkColor('w'),title=self.fingername[i]) )
                self.Xm.append( np.linspace(0, 0, self.windowWidth) )
                self.Rm.append(np.linspace(0, 0, self.windowWidth))
                self.ptr.append(0)

                self.plotGlove[i].getPlotItem().showGrid(x=True, y=True, alpha=0.5)
                # self.plotGlove[i].getPlotItem().setDownsampling(mode='peak')
                # self.plotGlove[i].getPlotItem().setClipToView(True)
                # self.plotGlove[i].getPlotItem().setRange(xRange=[-self.windowWidth, 0])
                # self.plotGlove[i].getPlotItem().setLimits(xMax=0)

                self.valMin.append(0)
                self.valMax.append(0)
                self.scaleMin.append(0)
                self.scaleMax.append(0)

        # Connect the signal
        self.threadkill = Event()
        self.data_acquired.connect(self.update_data)

        #self.gs = gs.GloveSckETH(self.data_acquired.emit, self.threadkill)
        self.gs = gs.GloveSckETH(self.data_acquired.emit, self.threadkill)
        self.gs.start()

    def placeWidgets(self):
        ## Create a grid layout to manage the widgets size and position
        self.layout = QtGui.QGridLayout()
        self.w.setLayout(self.layout)

        ## Add widgets to the layout in their proper positions
        self.layout.addWidget(self.pic, 0, 0)  # button goes in upper-left
        self.layout.addWidget(self.btn0, 2, 0)  # button goes in upper-left
        self.layout.addWidget(self.btn100, 3, 0)  # button goes after first button
        self.layout.addWidget(self.btnclr, 4, 0)  # button goes after first button
        # self.layout.addWidget(self.text, 2, 0)   # text edit goes in middle-left
        self.layout.addWidget(self.listw, 5, 0,1,2)  # list widget goes in bottom-left

        for i in range(0, NUM_SENSORS):
            self.layout.addWidget(self.plotGlove[i], i, 1)  # plot goes on right side, spanning 3 rows
            self.firstTime.append( False )

    def __init__(self):
        self.windowWidth = 1000  # width of the window displaying the curve
        self.Xm = []
        self.Rm = []
        self.ptr = []
        self.firstTime = []
        self.plotGlove = []
        self.colorg = ['#0000FF', '#FF0000', '#CA1F7B','#008C00', '#ED872D']
        self.fingername = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
        self.valMin=[]
        self.valMax=[]
        self.scaleMin=[]
        self.scaleMax=[]
        self.pointsToUpdate=5

        self.fingername = self.fingername[::-1]

        self.app = QtGui.QApplication([])

        super().__init__()

        self.createWidgets()
        self.createPlotWidgets()
        self.placeWidgets()

        ## Display the widget as a new window
        self.w.setWindowTitle( 'TU CHEMNITZ/MST - App for strain sensor fibers based electronic glove' )
        self.w.show()

        ## Start the Qt event loop
        self.app.exec_()

    # Slot to receive acquired data and update plot
    @pyqtSlot(np.ndarray)
    def update_data(self, data):
        if(len(data) <= NUM_SENSORS):
            for i in range(0,NUM_SENSORS):
                #print(data[i])
                self.Rm[i][:-1] = self.Rm[i][1:]  # shift data in the temporal mean 1 sample left
                self.Rm[i][-1] = data[i]

                self.Xm[i][:-1] = self.Xm[i][1:]            # shift data in the temporal mean 1 sample left
                self.Xm[i][-1] = self.scale( data[i], i )    # vector containing the instantaneous values
                self.ptr[i]+=1
                if( self.ptr[i] > self.pointsToUpdate ):
                    self.plotGlove[i].getPlotItem().clear()
                    self.plotGlove[i].plot( self.Xm[i],pen=pg.mkPen(self.colorg[i], width=2, symbol='o') )
                    self.firstTime[i] = True
                    self.ptr[i] = 0
        return

    # Slot to receive acquired data and update plot
    @pyqtSlot(np.ndarray)
    def update_data2(self, data):
        if(len(data) <= NUM_SENSORS):
            for i in range(0,NUM_SENSORS):
                #print(data[i])
                self.Rm[i][:-1] = self.Rm[i][1:]  # shift data in the temporal mean 1 sample left
                self.Rm[i][-1] = data[i]

                self.Xm[i][self.ptr[i]] = self.scale( data[i], i )
                self.ptr[i]+=1
                if(self.ptr[i] >= self.Xm[i].shape[0] ):
                    tmp = self.Xm[i]
                    self.Xm[i] = np.empty(self.Xm[i].shape[0]*2)
                    self.Xm[i][:tmp.shape[0]] = tmp

                if( self.firstTime[i] == False ):
                    self.plotGlove[i].getPlotItem().clear()
                    self.plotGlove[i].plot(self.Xm[i][:self.ptr[i]],pen=pg.mkPen(self.colorg[i], width=2, symbol='o'))
                    self.plotGlove[i].getPlotItem().setPos( -self.ptr[i], 0)
                    self.firstTime[i] = True
                else:
                    self.plotGlove[i].getPlotItem().clear()
                    self.plotGlove[i].getPlotItem().plot( self.Xm[i][:self.ptr[i]] )
                    self.plotGlove[i].getPlotItem().setPos( -self.ptr[i], 0)
        return


    def scale(self, data, idx):
        if self.scaleMax[idx] == self.scaleMin[idx]:
            return data
        else:
            s = (data-self.valMin[idx])*(self.scaleMax[idx]-self.scaleMin[idx])/(self.valMax[idx]-self.valMin[idx]) + self.scaleMin[idx]
            s = max(s, self.scaleMin[idx])
            s = min(s, self.scaleMax[idx])
        return s

    def onClickBtn0(self,checked):
        print('Calibrate for 0%')
        for i in range(0,NUM_SENSORS):
            self.scaleMin[i] = 0
            self.valMin[i] = self.Rm[i][-1]
            self.plotGlove[i].getPlotItem().setYRange(self.scaleMin[i], self.scaleMax[i])
        self.listw.addItem('Calibrated 0%')

    def onClickBtn100(self,checked):
        print('Calibrate for 100%')
        for i in range(0,NUM_SENSORS):
            self.scaleMax[i] = 100
            self.valMax[i] = self.Rm[i][-1]
            self.plotGlove[i].getPlotItem().setYRange(self.scaleMin[i], self.scaleMax[i])
        self.listw.addItem('Calibrated 100%')

    def onClickBtnClear(self,checked):
        print('Calibration cleared')
        for i in range(0,NUM_SENSORS):
            self.scaleMax[i] = 0
            self.scaleMin[i] = 0
            self.plotGlove[i].getPlotItem().autoRange()
        self.listw.addItem('Calibration Cleared')

if __name__ == '__main__':
    c = App()
    c.close()