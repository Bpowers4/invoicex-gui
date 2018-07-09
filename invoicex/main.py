import sys
from PyQt5.QtWidgets import QApplication

import subprocess
import os
from distutils import spawn
import shutil

from facturx import *
import json
from datetime import datetime as dt

from PyQt5.QtWidgets import (QMainWindow, QAction, QFileDialog, QLineEdit,
                             QLabel, QDockWidget, QSizePolicy, QGridLayout,
                             QScrollArea, QWidget, QMessageBox, QPushButton)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QEvent


class InvoiceX(QMainWindow):

    def __init__(self):
        super().__init__()

        self.mainWindowLeft = 300
        self.mainWindowTop = 300
        self.mainWindowWidth = 680
        self.mainWindowHeight = 480

        self.fileLoaded = False
        self.dialog = None
        self.initUI()

    def initUI(self):

        # StatusBar

        self.statusBar()
        self.setStatusTip('Select a PDF to get started')
        self.set_menu_bar()
        self.set_dockview_fields()
        self.set_center_widget()
        self.set_toolbar()

        self.setGeometry(self.mainWindowLeft, self.mainWindowTop,
                         self.mainWindowWidth, self.mainWindowHeight)
        self.setWindowTitle('Invoice-X')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__),
                                              'icons/logo.ico')))
        self.show()

        if not spawn.find_executable('convert'):
            QMessageBox.critical(self, 'Import Error',
                                 "Imagemagick is not installed",
                                 QMessageBox.Ok)

    def set_toolbar(self):
        toolbar = self.addToolBar('File')
        toolbar.addAction(self.openFile)
        toolbar.addAction(self.saveFile)
        toolbar.addAction(self.validateMetadata)
        toolbar.addAction(self.editFields)

    def set_center_widget(self):
        self.square = QLabel(self)
        self.square.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.square)

    def set_dockview_fields(self):
        self.fields = QDockWidget("Fields", self)
        self.fields.installEventFilter(self)
        self.fieldsQWidget = QWidget()
        self.fieldsScrollArea = QScrollArea()
        self.fieldsScrollArea.setWidgetResizable(True)
        self.fieldsScrollArea.setWidget(self.fieldsQWidget)

        self.layout = QGridLayout()
        self.fieldsQWidget.setLayout(self.layout)

        self.fields.setWidget(self.fieldsScrollArea)
        self.fields.setFloating(False)
        self.fields.setMinimumWidth(360)
        self.fields.setStyleSheet("QWidget { background-color: #AAB2BD}")
        self.addDockWidget(Qt.RightDockWidgetArea, self.fields)

    def set_menu_bar(self):
        self.exitAct = QAction(QIcon(os.path.join(
            os.path.dirname(__file__), 'icons/exit.png')), 'Exit', self)
        self.exitAct.setShortcut('Ctrl+Q')
        self.exitAct.setStatusTip('Exit application')
        self.exitAct.triggered.connect(self.close)

        self.openFile = QAction(QIcon(os.path.join(
            os.path.dirname(__file__), 'icons/pdf.png')), 'Open', self)
        self.openFile.setShortcut('Ctrl+O')
        self.openFile.setStatusTip('Open new File')
        self.openFile.triggered.connect(self.show_file_dialog)

        self.saveFile = QAction(QIcon(os.path.join(
            os.path.dirname(__file__), 'icons/save.png')), 'Save', self)
        self.saveFile.setShortcut('Ctrl+S')
        self.saveFile.setStatusTip('Save File')
        self.saveFile.triggered.connect(self.save_file_dialog)

        self.saveAsFile = QAction('Save As', self)
        self.saveAsFile.setStatusTip('Save File as a new File')
        self.saveAsFile.triggered.connect(self.show_save_as_dialog)

        self.viewDock = QAction('View Fields', self, checkable=True)
        self.viewDock.setStatusTip('View Fields')
        self.viewDock.setChecked(True)
        self.viewDock.triggered.connect(self.view_dock_field_toggle)

        extractFields = QAction('Extract Fields', self)
        extractFields.setStatusTip('Extract Fields from PDF and add to XML')
        extractFields.triggered.connect(self.extract_fields_from_pdf)

        jsonFormat = QAction('JSON', self)
        jsonFormat.setStatusTip('Export file to JSON')
        jsonFormat.triggered.connect(lambda: self.export_fields('json'))

        xmlFormat = QAction('XML', self)
        xmlFormat.setStatusTip('Export file to XML')
        xmlFormat.triggered.connect(lambda: self.export_fields('xml'))

        ymlFormat = QAction('YML', self)
        ymlFormat.setStatusTip('Export file to YML')
        ymlFormat.triggered.connect(lambda: self.export_fields('yml'))

        self.validateMetadata = QAction(QIcon(os.path.join(
            os.path.dirname(__file__), 'icons/validate.png')),
            'Validate', self)
        self.validateMetadata.setStatusTip('Validate XML')
        self.validateMetadata.triggered.connect(self.validate_xml)

        addMetadata = QAction('Add Metadata', self)
        addMetadata.setStatusTip('Add metadata to PDF')

        self.editFields = QAction(QIcon(
            os.path.join(os.path.dirname(__file__), 'icons/edit.png')),
            'Edit Metadata', self)
        self.editFields.setStatusTip('Edit Metadata in XML')
        self.editFields.triggered.connect(self.edit_fields_dialog)

        documentation = QAction('Documentation', self)
        documentation.setStatusTip('Open Documentation for Invoice-X')
        documentation.triggered.connect(self.documentation_menubar)

        aboutApp = QAction('About', self)
        aboutApp.setStatusTip('Know about Invoice-X')
        aboutApp.triggered.connect(self.about_app_menubar)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(self.openFile)
        fileMenu.addAction(self.saveFile)
        fileMenu.addAction(self.saveAsFile)
        fileMenu.addAction(self.viewDock)
        fileMenu.addAction(self.exitAct)

        commandMenu = menubar.addMenu('&Command')

        exportMetadata = commandMenu.addMenu('&Export Metadata')
        exportMetadata.addAction(jsonFormat)
        exportMetadata.addAction(xmlFormat)
        exportMetadata.addAction(ymlFormat)

        commandMenu.addAction(self.validateMetadata)
        commandMenu.addAction(self.editFields)
        commandMenu.addAction(addMetadata)
        commandMenu.addAction(extractFields)

        helpMenu = menubar.addMenu('&Help')
        helpMenu.addAction(documentation)
        helpMenu.addAction(aboutApp)

    def view_dock_field_toggle(self, state):
        if state:
            self.fields.show()
        else:
            self.fields.hide()

    def validate_xml(self):
        try:
            if self.factx.is_valid():
                QMessageBox.information(self, 'Valid XML',
                                        "The XML is Valid",
                                        QMessageBox.Ok)
            else:
                QMessageBox.critical(self, 'Invalid XML',
                                     "The XML is invalid",
                                     QMessageBox.Ok)
        except AttributeError:
            QMessageBox.critical(self, 'File Not Found',
                                 "Load a PDF first",
                                 QMessageBox.Ok)

    def set_pdf_preview(self):
        # print(str(fileName[0]))
        if not os.path.exists('.load'):
            os.mkdir('.load')
        if sys.platform[:3] == 'win':
            convert = ['magick', self.fileName[0],
                       '-flatten', '.load/preview.jpg']
        else:
            convert = ['convert', '-verbose', '-density', '150', '-trim',
                       self.fileName[0], '-quality', '100', '-flatten',
                       '-sharpen', '0x1.0', '.load/preview.jpg']
        subprocess.call(convert)
        self.pdfPreviewImage = '.load/preview.jpg'
        self.fileLoaded = True
        self.square.setPixmap(QPixmap(self.pdfPreviewImage).scaled(
            self.square.size().width(), self.square.size().height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def edit_fields_dialog(self):
        try:
            self.dialog = EditFieldsClass(self.factx,
                                          self.fieldsDict,
                                          self.metadata_field)
            self.dialog.installEventFilter(self)
            # self.dialog.show()
        except AttributeError:
            QMessageBox.critical(self, 'File Not Found',
                                 "Load a PDF first",
                                 QMessageBox.Ok)

    def update_dock_fields(self):
        self.factx.write_json('.load/output.json')
        with open('.load/output.json') as jsonFile:
            self.fieldsDict = json.load(jsonFile)
        os.remove('.load/output.json')
        # print(self.fieldsDict)

        i = 0

        self.metadata_field = {
            'amount_tax': 'Amount Tax',
            'amount_total': 'Amount Total',
            'amount_untaxed': 'Amount Untaxed',
            'buyer': 'Buyer',
            'currency': 'Currency',
            'date': 'Date',
            'date_due': 'Date Due',
            'invoice_number': 'Invoice Number',
            'name': 'Name',
            'notes': 'Notes',
            'seller': 'Seller',
            'type': 'Type',
            'version': 'Version'
        }

        for key in sorted(self.fieldsDict):
            i += 1
            try:
                self.factx[key]
            except IndexError:
                self.fieldsDict[key] = "Field Not Specified"
            except TypeError:
                pass
            fieldKey = QLabel(self.metadata_field[key] + ": ")
            if self.fieldsDict[key] is None:
                fieldValue = QLabel("NA")
            else:
                if key[:4] == "date" and \
                        self.fieldsDict[key] != "Field Not Specified":
                    self.fieldsDict[key] = self.fieldsDict[key][:4] \
                        + "/" + self.fieldsDict[key][4:6] \
                        + "/" + self.fieldsDict[key][6:8]
                if self.fieldsDict[key] == "Field Not Specified":
                    fieldValue = QLabel(self.fieldsDict[key])
                    fieldValue.setStyleSheet("QLabel { color: #666666}")
                else:
                    fieldValue = QLabel(self.fieldsDict[key])
            # fieldValue.setFrameShape(QFrame.Panel)
            # fieldValue.setFrameShadow(QFrame.Plain)
            # fieldValue.setLineWidth(3)
            self.layout.addWidget(fieldKey, i, 0)
            self.layout.addWidget(fieldValue, i, 1)

    def show_file_dialog(self):

        self.fileName = QFileDialog.getOpenFileName(self, 'Open file',
                                                    os.path.expanduser("~"),
                                                    "pdf (*.pdf)")

        if self.fileName[0]:
            # print(fileName[0])
            self.factx = FacturX(self.fileName[0])
            self.set_pdf_preview()
            self.update_dock_fields()
            self.setStatusTip("PDF is Ready")

            # self.file_selected.setText(str(fname[0][0]))
            # self.file_names = fname[0]

    def save_file_dialog(self):
        if self.fileLoaded:
            if self.confirm_save_dialog():
                self.factx.write_pdf(self.fileName[0])
        else:
            QMessageBox.critical(self, 'File Not Found',
                                 "Load a PDF first",
                                 QMessageBox.Ok)

    def confirm_save_dialog(self):
        reply = QMessageBox.question(
            self, 'Message', "Do you want to save? This cannot be undone",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            return True
        else:
            return False

    def show_save_as_dialog(self):
        if self.fileLoaded:
            self.saveFileName = QFileDialog.getSaveFileName(
                self, 'Save file', os.path.expanduser("~"), "pdf (*.pdf)")
            if self.saveFileName[0]:
                if self.saveFileName[0].endswith('.pdf'):
                    fileName = self.saveFileName[0]
                else:
                    fileName = self.saveFileName[0] + '.pdf'
                self.factx.write_pdf(fileName)
        else:
            QMessageBox.critical(self, 'File Not Found',
                                 "Load a PDF first",
                                 QMessageBox.Ok)

    def extract_fields_from_pdf(self):
        pass

    def documentation_menubar(self):
        pass

    def about_app_menubar(self):
        pass

    def export_fields(self, outputformat):
        if self.fileLoaded:
            self.exportFileName = QFileDialog.getSaveFileName(
                self, 'Export file',
                os.path.expanduser("~") +
                '/output.%s' % outputformat,
                "%s (*.%s)" % (outputformat, outputformat))
            if self.exportFileName[0]:
                if outputformat is "json":
                    self.factx.write_json(self.exportFileName[0])
                elif outputformat is "xml":
                    self.factx.write_xml(self.exportFileName[0])
                elif outputformat is "yml":
                    self.factx.write_yml(self.exportFileName[0])
        else:
            QMessageBox.critical(self, 'File Not Found',
                                 "Load a PDF first",
                                 QMessageBox.Ok)

    def resizeEvent(self, event):
        if self.fileLoaded:
            self.square.setPixmap(QPixmap(self.pdfPreviewImage).scaled(
                self.square.size().width(), self.square.size().height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.square.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Ignored)
            QMainWindow.resizeEvent(self, event)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Close and source is self.fields:
            self.viewDock.setChecked(False)

        if event.type() == QEvent.Close and source is self.dialog:
            self.update_dock_fields()
        return QMainWindow.eventFilter(self, source, event)

    def closeEvent(self, event):
        if os.path.isdir('.load'):
            shutil.rmtree('.load/')


class EditFieldsClass(QWidget, object):
    def __init__(self, factx, fieldsDict, metadataDict):
        super().__init__()
        self.fDict = fieldsDict
        self.mDict = metadataDict
        self.factx = factx
        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        i = 0
        self.fieldsKeyList = []
        self.fieldsValueList = []
        for key in sorted(self.fDict):
            i += 1
            fKey = QLabel(self.mDict[key])
            fValue = QLineEdit()
            fValue.setText(self.fDict[key])
            if self.fDict[key] == "Field Not Specified":
                fValue.setEnabled(False)
            else:
                self.fieldsKeyList.append(key)
                self.fieldsValueList.append(fValue)
            layout.addWidget(fKey, i, 0)
            layout.addWidget(fValue, i, 1)

        i = i + 1
        saveButton = QPushButton('Apply')
        saveButton.clicked.connect(self.update_fields_and_dock)
        discardButton = QPushButton('Discard')
        discardButton.clicked.connect(self.discard_fields)
        layout.addWidget(discardButton, i, 0)
        layout.addWidget(saveButton, i, 1)

        self.setLayout(layout)
        self.move(300, 150)
        self.setWindowTitle('Edit Fields')
        self.setWindowIcon(QIcon('icons/logo.png'))
        self.show()

    def update_fields_and_dock(self):
        try:
            for key, value in zip(self.fieldsKeyList, self.fieldsValueList):
                if key[:4] != "date":
                    self.factx[key] = value.text()
                else:
                    self.factx[key] = dt.strptime(value.text(), '%Y/%m/%d')
            self.close()
        except ValueError:
            QMessageBox.critical(self, 'Invalid Field Value',
                                 "Invalid Field Value(s)",
                                 QMessageBox.Ok)

    def discard_fields(self):
        self.close()


def main():
    app = QApplication(sys.argv)
    InvoiceX()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
