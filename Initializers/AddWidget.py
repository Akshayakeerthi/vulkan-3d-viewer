from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class propSettings(QDockWidget):
    
    def __init__(self, Name, parent = None):
        super().__init__(parent)
        self.QString = Name
        
        widget = QWidget()
        widget.setStyleSheet("background-color: rgba(69,69,69,255); border-radius: 10px;")
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        title = QLabel(Name)
        
        btn_size = 20
        
        self.btn_close = QPushButton("x")
        self.btn_close.clicked.connect(self.btn_close_clicked)
        self.btn_close.setFixedSize(btn_size,btn_size)
        self.btn_close.setStyleSheet("background-color: red;")
        
        self.btn_max = QPushButton("+")
        self.btn_max.clicked.connect(self.btn_max_clicked)
        self.btn_max.setFixedSize(btn_size, btn_size)
        self.btn_max.setStyleSheet("background-color: gray;")
        
        title.setFixedHeight(35)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)
        widget.setLayout(layout)
        self.setTitleBarWidget(widget)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: rgba(0,0,0,1); border: 3px darkGray; border-radius: 5px;")
        parent.addDockWidget(Qt.RightDockWidgetArea, self)
        
    def btn_close_clicked(self):
        self.close()
    
    def btn_max_clicked(self):
        self.showMaximized()
        
        #return dock