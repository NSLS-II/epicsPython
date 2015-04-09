"""
selfCreates a GUI window to calibrate 2-theta for an Mca.

Author:         Mark Rivers
Created:        Sept. 18, 2002
Modifications:  MLR, Sept. 20, 2002.  Numerous bug fixes.
"""
from Tkinter import *
import copy
import tkMessageBox
import Pmw
import Mca
import Numeric
import math
import CARSMath
import BltPlot
import jcpds
import MLab

############################################################
class mcaCalibrate2theta_widgets:
   """ Private class"""
   def __init__(self, nrois):
      self.use_flag             = range(nrois)
      self.d_spacing            = range(nrois)
      self.fwhm                 = range(nrois)
      self.energy               = range(nrois)
      self.label                = range(nrois)
      self.two_theta            = range(nrois)
      self.two_theta_diff       = range(nrois)
      self.two_theta_fit        = range(nrois)

class mcaCalibrate2theta:
   def __init__(self, mca, command=None):
      """
      Creates a new GUI window for calibrating 2-theta for an Mca object.

      Inputs:
         mca:
            An Mca instance to be calibrated.  The Mca must have at least 1
            Regions of Interest (ROI) defined.

      Keywords:
         command:
            A callback command that will be executed if the OK button on
            the GUI window is pressed.  The callback will be invoked as:
               command(exit_status)
            where exit_status is 1 if OK was pressed, and 0 if Cancel was
            pressed or the window was closed with the window manager.

      Procedure:
         The calibration is done by determining the centroid position and
         d-spacing of each ROI.

         The centroids positions are computed by fitting the
         ROI counts to a Gaussian, using CARSMath.fit_gaussian.

         The d-spacing the ROI can be entered manually in the GUI window, or it
         can be determined automatically if the label of the ROI can be
         successfully used in jcpds.lookup_jcpds_line().

         Each ROI can be selectively used or omitted when doing the calibration.

         The errors in the 2-theta calibration, can be plotted using BltPlot.
      """
      self.input_mca = mca
      self.mca = copy.deepcopy(mca)
      self.exit_command = command
      self.roi = self.mca.get_rois()
      self.nrois = len(self.roi)
      if (self.nrois < 1):
         tkMessageBox.showerror(title='mcaCalibrate2theta Error', 
                message='Must have at least one ROI to perform calibration')
         return
      self.calibration = self.mca.get_calibration()
      self.fwhm_chan   = Numeric.zeros(self.nrois, Numeric.Float)
      self.two_theta   = Numeric.zeros(self.nrois, Numeric.Float)
      self.widgets     = mcaCalibrate2theta_widgets(self.nrois)
      self.data        = self.mca.get_data()

      # Compute the centroid and FWHM of each ROI
      for i in range(self.nrois):
         left = self.roi[i].left
         right = self.roi[i].right
         total_counts = self.data[left:right+1]
         n_sel        = right - left + 1
         sel_chans    = left + Numeric.arange(n_sel)
         left_counts  = self.data[left]
         right_counts = self.data[right]
         bgd_counts   = (left_counts + Numeric.arange(float(n_sel))/(n_sel-1) *
                                     (right_counts - left_counts))
         net_counts   = total_counts - bgd_counts
         net          = Numeric.sum(net_counts)
 
         if ((net > 0.) and (n_sel >= 3)):
            amplitude, centroid, fwhm = CARSMath.fit_gaussian(sel_chans,
                                                              net_counts)
            self.roi[i].centroid = centroid
            self.fwhm_chan[i] = fwhm
         else:
            self.roi[i].centroid = (left + right)/2.
            self.fwhm_chan[i] = right-left
         self.roi[i].fwhm = (self.mca.channel_to_energy(self.roi[i].centroid + 
                                          self.fwhm_chan[i]/2.) - 
                             self.mca.channel_to_energy(self.roi[i].centroid - 
                                          self.fwhm_chan[i]/2.))
         self.roi[i].energy = self.mca.channel_to_energy(self.roi[i].centroid)

      self.widgets.top = t = Pmw.Dialog(command=self.menu_ok_cancel,
                     buttons=('OK', 'Apply', 'Cancel'),
                     title='mcaCalibrate2theta')
      top = t.component('dialogchildsite')
      box = Frame(top, borderwidth=1, relief=SOLID); box.pack(fill=X, pady=3)

      t = Label(box, text='ROI');               t.grid(row=0, column=0)
      t = Label(box, text='Use?');              t.grid(row=0, column=1)
      t = Label(box, text='Energy');            t.grid(row=0, column=2)
      t = Label(box, text='FWHM');              t.grid(row=0, column=3)
      t = Label(box, text='D-spacing');         t.grid(row=0, column=4)
      t = Label(box, text='HKL');               t.grid(row=0, column=5)
      t = Label(box, text='Two-theta');         t.grid(row=0, column=6)
      t = Label(box, text='Two-theta diff.');   t.grid(row=0, column=7)
      text_width=10
      for i in range(self.nrois):
         row=i+1
         t = Label(box, text=str(i)); 
         t.grid(row=row, column=0)
         self.widgets.use_flag[i] = t = Pmw.OptionMenu(box,
                        items=('No','Yes'),
                        initialitem = self.roi[i].use,
                        command=lambda e, s=self, r=i: s.menu_use(e,r))
         t.grid(row=row, column=1)
         self.widgets.energy[i] = t = Pmw.EntryField(box, 
                        value=('%.3f' % self.roi[i].energy),
                        entry_width=text_width, entry_justify=CENTER, 
                        command=lambda s=self, r=i: s.menu_energy(r))
         t.grid(row=row, column=2)
         self.widgets.fwhm[i] = t = Label(box, 
                            text=('%.3f' % self.roi[i].fwhm), width=text_width,
                            justify=CENTER, borderwidth=1, relief=SOLID)
         t.grid(row=row, column=3)
         d = jcpds.lookup_jcpds_line(self.roi[i].label)
         if (d != None): self.roi[i].d_spacing = d
         self.widgets.d_spacing[i] = t = Pmw.EntryField(box, 
                        value=('%.3f' % self.roi[i].d_spacing),
                        entry_width=text_width, entry_justify=CENTER, 
                        command=lambda s=self, r=i: s.menu_d_spacing(r))
         t.grid(row=row, column=4)
         self.widgets.label[i] = t = Pmw.EntryField(box, 
                        value=str(self.roi[i].label),
                        entry_width=text_width, entry_justify=CENTER, 
                        command=lambda s=self, r=i: s.menu_label(r))
         t.grid(row=row, column=5)

         self.widgets.two_theta[i] = t = Label(box, 
                            text=('%.3f' % self.two_theta[i]), width=text_width,
                            justify=CENTER, borderwidth=1, relief=SOLID)
         t.grid(row=row, column=6)
         self.widgets.two_theta_diff[i] = t = Label(box, 
                            text=('%.3f' % 0.0), width=text_width,
                            justify=CENTER, borderwidth=1, relief=SOLID)
         t.grid(row=row, column=7)

      row = Frame(top, borderwidth=1, relief=SOLID); row.pack(fill=X, pady=3)
      self.widgets.do_fit = t = Button(row, text='Compute 2-theta', 
                                        command=self.menu_do_fit)
      t.pack(side=LEFT, anchor=S)
      self.widgets.plot_cal = t = Button(row, text='Plot 2-theta error',
                                        command=self.menu_plot_calibration)
      t.pack(side=LEFT, anchor=S)
      self.widgets.two_theta_fit = t = Pmw.EntryField(row, 
                            label_text='Two-theta', labelpos=W,
                            value=self.calibration.two_theta,
                            entry_width=20, entry_justify=CENTER, 
                            command=self.menu_two_theta)
      t.pack(side=LEFT)
      self.menu_do_fit()

   def menu_two_theta(self):
      """ Private method """
      two_theta = float(self.widgets.two_theta.get())
      self.calibration.two_theta = two_theta
      self.widgets.two_theta.setentry('%.3f' % two_theta)

   def menu_plot_calibration(self):
      """ Private method """
      energy = []
      two_theta_diff = []
      energy_use = []
      two_theta_diff_use = []
      for i in range(self.nrois):
         energy.append(self.roi[i].energy)
         two_theta_diff.append(self.two_theta[i] - self.calibration.two_theta)
         if (self.roi[i].use):
            energy_use.append(energy[i])
            two_theta_diff_use.append(two_theta_diff[i])
      
      p = BltPlot.BltPlot(energy, two_theta_diff, symbol="circle",
                  title='MCA Two-theta error', linewidth=0,
                  xtitle='Energy', ytitle='Two-theta error', legend=1,
                  label='All points')
      p.oplot(energy_use, two_theta_diff_use, symbol="square", linewidth=1,
                  label='Points used')

   def menu_energy(self, roi):
      """ Private method """
      energy = float(self.widgets.energy[roi].get())
      self.roi[roi].energy = energy
      self.widgets.energy[roi].setentry('%.3f' % energy)
      self.menu_do_fit()

   def menu_d_spacing(self, roi):
      """ Private method """
      d_spacing = float(self.widgets.d_spacing[roi].get())
      self.roi[roi].d_spacing = d_spacing
      self.widgets.d_spacing[roi].setentry('%.3f' % d_spacing)
      self.menu_do_fit()

   def menu_use(self, value, roi):
      """ Private method """
      self.roi[roi].use = (value == 'Yes')
      self.menu_do_fit()

   def menu_label(self, roi):
      """ Private method """
      label = self.widgets.label[roi].get()
      d_spacing = jcpds.lookup_jcpds_line(label)
      if (d_spacing != None):
         self.roi[roi].d_spacing = d_spacing
         self.widgets.d_spacing[roi].setentry('%.3f' % d_spacing)
         self.menu_do_fit()
      self.roi[roi].label=label

   def menu_do_fit(self):
      """ Private method """
      # Compute 2-theta for each ROI
      for i in range(self.nrois):
         if (self.roi[i].energy == 0) or (self.roi[i].d_spacing == 0):
            self.two_theta[i] = 0.
         else:
            self.two_theta[i] = 2.0 * math.asin(12.398 / 
               (2.0*self.roi[i].energy*self.roi[i].d_spacing))*180./math.pi
         self.widgets.two_theta[i].configure(text=('%.5f' % self.two_theta[i]))
      # Find which ROIs should be used for the calibration
      use = []
      for i in range(self.nrois):
         if (self.roi[i].use): use.append(i)
      nuse = len(use)
      if (nuse < 1):
         tkMessageBox.showerror(title='mcaCalibateEnergy Error', 
            message='Must have at least one valid point for calibration')
         return
      two_theta=[]
      for u in use:
         two_theta.append(self.two_theta[u])
      self.calibration.two_theta = MLab.mean(two_theta)
      sdev = MLab.std(two_theta)
      self.widgets.two_theta_fit.setentry(
                                 ('%.5f' % self.calibration.two_theta)
                                 + ' +- ' + ('%.5f' % sdev))
      for i in range(self.nrois):
         two_theta_diff = self.two_theta[i] - self.calibration.two_theta
         self.widgets.two_theta_diff[i].configure(text=('%.5f' % two_theta_diff))
      self.mca.set_calibration(self.calibration)

   def menu_ok_cancel(self, button):
      """ Private method """
      if (button == 'OK') or (button == 'Apply'):
         # Copy calibration and rois to input mca object
         self.input_mca.set_calibration(self.calibration)
         self.input_mca.set_rois(self.roi)
      if (button == 'OK'):
         exit_status = 1
      elif (button == 'Apply'):
         return
      else:
         exit_status = 0
      if (self.exit_command): self.exit_command(exit_status)
      self.widgets.top.destroy()
