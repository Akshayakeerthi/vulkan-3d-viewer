#!/usr/bin/env python
# coding: utf-8

# In[1]:


from Body import *
from PyQt5.Qt import QStandardItemModel, QStandardItem, QAction, QMenu
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QColor
from PyQt5.QtCore import *
import numpy as np


# In[2]:


class StandardItemModel(QStandardItemModel):
        
    def __init__(self, parent = None):
        super().__init__(parent)
        self.parent = parent
    
    def setData(self, index, value, role = QtCore.Qt.EditRole):
        
        
        if role == QtCore.Qt.EditRole:
            item = self.parent.treeModel.itemFromIndex(index)
            ful_v = self.parent.getParents(item, item.text())
            new_id = ful_v[:]
            for i in reversed(range(len(ful_v))):
                if ful_v[i] == '_':
                    break
                
                new_id = new_id.rstrip(ful_v[i])
            new_id += value
            accept = self.checkName(item, ful_v, new_id)
            
            if accept:
                if item.data() == 'Collection':
                    for i in range(item.rowCount()):
                        #i_Adrs = self.parent.getParents(item.child(i), item.child(i).text())
                        self.parent.delCollection(item.child(i), item, new_id + '_' + item.child(i).text())
                        
                else:
                    self.parent.delCollection(item, item.parent(), new_id)
                val = super(StandardItemModel, self).setData(index, value, role)
                
                return val
            else:
                return False
    
    def checkName(self, item, name, value, new_itm = None):
        
        if item.parent():
            lst = [self.parent.getParents(item.parent().child(i), item.parent().child(i).text()) for i in range(item.parent().rowCount())]
        else:
            lst = [self.parent.treeModel.item(i).text() for i in range(self.parent.treeModel.rowCount())]
        
        if not new_itm:
            lst.remove(name)
        
        if value in lst:
            msg = QMessageBox()
            msg.setWindowTitle("Creator PopUp")
            msg.setText("Name already exist!")
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setDefaultButton(QMessageBox.Ok)
            msg.setInformativeText("Try another name please....")
            
            msg.exec()
            return False
            
        else:
            return True
        
class SceneList(QTreeView):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.p = parent
        self.setHeaderHidden(True)
        self.setDragDropMode(4)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)
        self.setStyleSheet("show-decoration-selected: 1;paint-alternating-row-colors-for-empty-area: 1;color: rgba(184,184,184,255); alternate-background-color: rgba(53,53,53,255); background-color:rgba(66,66,66,255);")
        self.treeModel = StandardItemModel(self)
        self.setSelectionMode(QAbstractItemView.SelectionMode(3))
        self.rootNode = self.treeModel.invisibleRootItem()
        l = parent.widget.models3d
        
        for i, j in l.items():
            a = QStandardItem(i)
            self.rootNode.appendRow(a)
        self.setModel(self.treeModel)
        self.selectionModel().selectionChanged.connect(self.itemSelector)
        self.expandAll()
    
    def itemSelector(self, selected, deselected):
        
        self.p.widget.selectedItems = []
        for i in self.selectedIndexes():
            self.p.widget.selectedItems.append(i.data())
    
    def dragMoveEvent(self, event):
        prnt = self.treeModel.itemFromIndex(self.indexAt(event.pos()))
        if prnt:
            if prnt.data() == 'Collection':
                event.accept()
            else:
                event.ignore()
                
        else:
            event.accept()
    
    def dropEvent(self, event):
        
        super().dropEvent(event)
        event.acceptProposedAction()
        prnt = self.treeModel.itemFromIndex(self.indexAt(event.pos()))
        for i in self.selectedIndexes():
            item = self.treeModel.itemFromIndex(i)
            if item.data() == 'Collection':
                new_id = self.getParents(item, item.text(), prnt)
                for j in range(item.rowCount()):
                    self.delCollection(item.child(j), item, new_id + '_' + item.child(j).text())
            else:
                new_id = self.getParents(item, item.text(), prnt)
                self.delCollection(item, prnt, new_id)
            
    def delCollection(self, item, iAdrs, new_n = None):
        
        del_n = self.getParents(item, item.text())
        if item.data() == 'Item':
            if new_n:
                self.p.widget.models3d[new_n] = self.p.widget.models3d[del_n]
                del self.p.widget.models3d[del_n]
            else:
                del self.p.widget.models3d[iAdrs]
                if item.parent():
                    item.parent().removeRow(item.row())
                self.rootNode.removeRow(item.row())
        elif item.data() == 'Light':
            if new_n:
                self.p.lights.lights[new_n] = self.p.widget.lights[del_n]
                del self.p.widget.lights[del_n]
            else:
                del self.p.widget.lights[iAdrs]
                if item.parent():
                    item.parent().removeRow(item.row())
                self.rootNode.removeRow(item.row())
        else:
            if new_n:
                for i in range(item.rowCount()):
                    i_Adrs = self.getParents(item.child(i), item.child(i).text())
                    self.delCollection(item.child(i), item, i_Adrs)
            else:
                for i in range(item.rowCount()):
                    i_Adrs = self.getParents(item.child(i), item.child(i).text())
                    self.delCollection(item.child(i), i_Adrs)
                if item.parent():
                    item.parent().removeRow(item.row())
                self.rootNode.removeRow(item.row())
        
    def getParents(self, item, text, prnt = None):
        if item.parent():
            p_Name = self.getParents(item.parent(), item.parent().text())
        elif prnt:
            p_Name = self.getParents(prnt, prnt.text())
        else:
            return text
        return p_Name + '_' + text
    
    def contextMenuEvent(self, event):
        if self.selectedIndexes():
            menu = QMenu(self)            
            idel = menu.addAction('Delete')
            action = menu.exec_(self.mapToGlobal(event))
            if action == idel:
                for i in self.selectedIndexes():
                    item = self.treeModel.itemFromIndex(i)
                    item_Adrs = self.getParents(item, item.text())
                    self.delCollection(item, item_Adrs)
        else:
            Mmenu = QMenu(self)
            Lmenu = QMenu('Add Light')
            Mmenu.addMenu(Lmenu)
            
            mc = Mmenu.addAction('Make Collection')
            pl = Lmenu.addAction('Point Light')
            dl = Lmenu.addAction('Directional Light')
            
            action = Mmenu.exec_(self.mapToGlobal(event))
            
            if action == mc:
                self.makeCollection()
            elif action == pl:
                n = QInputDialog.getText(self, 'Input Dialog', 'Enter your name:')
                if n[1] and n[0] != '':
                    a = QStandardItem(n[0])
                    a.setData('Light')
                    self.rootNode.appendRow(a)
                    self.p.widget.addLight(n[0], 'point')
            elif action == dl:
                n = QInputDialog.getText(self, 'Input Dialog', 'Enter your name:')
                if n[1] and n[0] != '':
                    a = QStandardItem(n[0])
                    a.setData('Light')
                    self.rootNode.appendRow(a)
                    self.p.widget.addLight(n[0], 'directional')
                
    
    def makeCollection(self):
        a = QStandardItem('Untitled Collection')
        a.setData('Collection')
        self.rootNode.appendRow(a)
            
    def newItem(self, name = 'Untitled Item'):
        
        if self.treeModel.rowCount():
            item = self.treeModel.item(0)
            ful_v = self.getParents(item, item.text())
            new_id = ful_v[:]
            for i in reversed(range(len(ful_v))):
                if i == '_':
                    break
                new_id = new_id.rstrip(ful_v[i])
            new_id += name
            if not self.treeModel.checkName(self.treeModel.item(0), ful_v, new_id, True):
                return False
        a = QStandardItem(name)
        a.setData('Item')
        self.rootNode.appendRow(a)
        
        return True
        


# In[3]:


class MyMainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MyMainWindow, self).__init__(parent)
        
        self.resize(1280, 720)
        self.widget = HelloTriangleApplication(self)
        self.setCentralWidget(self.widget)
        sshFile="Stylesheets/scroller.stylesheet"
        with open(sshFile,"r") as fh:
            self.setStyleSheet(fh.read())
        self.dock1 = propSettings("Scene Collection", self)
        self.dock2 = propSettings("Simple", self)
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tabs.addTab(self.tab1, "Geeks")
        self.tabs.setTabPosition(QTabWidget.West)
        
        self.sceneitems = SceneList(self)
        self.dock1.setWidget(self.sceneitems)
        self.tabs.setTabPosition(QTabWidget.West)
        self.dock2.setWidget(self.tabs)
        
        self.menuBar = self.menuBar()
        fileMenu = self.menuBar.addMenu('File')
        editMenu = self.menuBar.addMenu('Edit')
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(lambda : QApplication.quit())
        fileMenu.addAction(exit_action)
        
        openFile = QAction("&Import", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip('Open File')
        openFile.triggered.connect(self.file_open)
        fileMenu.addAction(openFile)
                
    def file_open(self):
        
        name = QFileDialog.getOpenFileName(self, 'Open File')
        
        if name[0]:
            n = QInputDialog.getText(self, 'Input Dialog', 'Enter your name:')
            
            if n[1] and n[0] != '':
                if not self.sceneitems.newItem(n[0]):
                    return
                
                self.widget.models3d[n[0]] = Model(self.widget.deviceInfo.device, self.widget.deviceInfo.physicalDevice,
                                                   self.widget.deviceInfo.commandPool, self.widget.deviceInfo.graphicQueue,
                                                   name[0])
                self.widget.models3d[n[0]].addTexture('CommonResources/Textures/wood.jpeg')
                updateDescriptorSet(self.widget.deviceInfo.device, len(self.widget.renderData['SwapChain'].RenderImages),
                                    self.widget.models3d[n[0]].textureImageView, self.widget.models3d[n[0]].textureSampler,
                                    self.widget.ubo, self.widget.uniformBuffer, self.widget.renderData['SwapChain'].descriptorSet)
                self.widget.createCommandBuffers()
                
        


# In[4]:


if __name__ == '__main__':
    import sys
    
    app = QApplication(sys.argv)
    
    win = MyMainWindow()
    win.show()
    
    def clenaup():
        
        global win
        
        #win.timer.stop()
        del win
    
    
    app.aboutToQuit.connect(clenaup)
    
    app.exec_()
    
    del app
    
    sys.exit()
