""" Function that adds common arguments for all input formats to the argument parser handle. """

# Copied from WMPL but adjusted to remove dependencies
# Copyright (C) 2018-2023 Mark McIntyre
# import os
import numpy as np
from Math import J2000_JD, jd2Date, equatorialCoordPrecession_vect, raDec2AltAz_vect


class MeteorObservation(object):
    """ Container for meteor observations. 
        
        The points in arrays are RA and Dec in J2000 epoch, in radians.

        Arguments:
            jdt_ref: [float] Reference Julian date when the relative time is t = 0s.
            station_id: [str] Station ID.
            latitude: [float] Latitude +N in radians.
            longitude: [float] Longitude +E in radians.
            height: [float] Elevation above sea level (MSL) in meters.
            fps: [float] Frames per second.

        Keyword arguments:
            ff_name: [str] Name of the originating FF file.

    """
    def __init__(self, jdt_ref, station_id, latitude, longitude, height, fps, ff_name=None):

        self.jdt_ref = jdt_ref
        self.station_id = station_id
        self.latitude = latitude
        self.longitude = longitude
        self.height = height
        self.fps = fps

        self.ff_name = ff_name

        self.frames = []
        self.time_data = []
        self.x_data = []
        self.y_data = []
        self.azim_data = []
        self.elev_data = []
        self.ra_data = []
        self.dec_data = []
        self.mag_data = []
        self.abs_mag_data = []



    def addPoint(self, frame_n, x, y, azim, elev, ra, dec, mag):
        """ Adds the measurement point to the meteor.

        Arguments:
            frame_n: [flaot] Frame number from the reference time.
            x: [float] X image coordinate.
            y: [float] X image coordinate.
            azim: [float] Azimuth, J2000 in degrees.
            elev: [float] Elevation angle, J2000 in degrees.
            ra: [float] Right ascension, J2000 in degrees.
            dec: [float] Declination, J2000 in degrees.
            mag: [float] Visual magnitude.

        """

        self.frames.append(frame_n)

        # Calculate the time in seconds w.r.t. to the reference JD
        point_time = float(frame_n)/self.fps

        self.time_data.append(point_time)

        self.x_data.append(x)
        self.y_data.append(y)

        # Angular coordinates converted to radians
        self.azim_data.append(np.radians(azim))
        self.elev_data.append(np.radians(elev))
        self.ra_data.append(np.radians(ra))
        self.dec_data.append(np.radians(dec))
        self.mag_data.append(mag)



    def finish(self):
        """ When the initialization is done, convert data lists to numpy arrays. """

        self.frames = np.array(self.frames)
        self.time_data = np.array(self.time_data)
        self.x_data = np.array(self.x_data)
        self.y_data = np.array(self.y_data)
        self.azim_data = np.array(self.azim_data)
        self.elev_data = np.array(self.elev_data)
        self.ra_data = np.array(self.ra_data)
        self.dec_data = np.array(self.dec_data)
        self.mag_data = np.array(self.mag_data)

        # Sort by frame
        temp_arr = np.c_[self.frames, self.time_data, self.x_data, self.y_data, self.azim_data, \
        self.elev_data, self.ra_data, self.dec_data, self.mag_data]
        temp_arr = temp_arr[np.argsort(temp_arr[:, 0])]
        self.frames, self.time_data, self.x_data, self.y_data, self.azim_data, self.elev_data, self.ra_data, \
            self.dec_data, self.mag_data = temp_arr.T




    def __repr__(self):

        out_str = ''

        out_str += 'Station ID = ' + str(self.station_id) + '\n'
        out_str += 'JD ref = {:f}'.format(self.jdt_ref) + '\n'
        out_str += 'DT ref = {:s}'.format(jd2Date(self.jdt_ref, \
            dt_obj=True).strftime("%Y/%m/%d-%H%M%S.%f")) + '\n'
        out_str += 'Lat = {:f}, Lon = {:f}, Ht = {:f} m'.format(np.degrees(self.latitude), 
            np.degrees(self.longitude), self.height) + '\n'
        out_str += 'FPS = {:f}'.format(self.fps) + '\n'

        out_str += 'Points:\n'
        out_str += 'Time, X, Y, azimuth, elevation, RA, Dec, Mag:\n'

        for point_time, x, y, azim, elev, ra, dec, mag in zip(self.time_data, self.x_data, self.y_data, \
            self.azim_data, self.elev_data, self.ra_data, self.dec_data, self.mag_data):

            if mag is None:
                mag = 0

            out_str += '{:.4f}, {:.2f}, {:.2f}, {:.2f}, {:.2f}, {:.2f}, {:+.2f}, {:.2f}\n'.format(point_time,\
                x, y, np.degrees(azim), np.degrees(elev), np.degrees(ra), np.degrees(dec), mag)


        return out_str



def prepareObservations(meteor_list):
    """ Takes a list of MeteorObservation objects, normalizes all data points to the same reference Julian 
        date, precesses the observations from J2000 to the epoch of date. 
    
    Arguments:
        meteor_list: [list] List of MeteorObservation objects

    Return:
        (jdt_ref, meteor_list):
            - jdt_ref: [float] reference Julian date for which t = 0
            - meteor_list: [list] A list a MeteorObservations whose time is normalized to jdt_ref, and are
                precessed to the epoch of date

    """

    if meteor_list:

        # The reference meteor is the one with the first time of the first frame
        ref_ind = np.argmin([met.jdt_ref + met.time_data[0]/86400.0 for met in meteor_list])
        tsec_delta = meteor_list[ref_ind].time_data[0] 
        jdt_delta = tsec_delta/86400.0


        ### Normalize all times to the beginning of the first meteor

        # Apply the normalization to the reference meteor
        meteor_list[ref_ind].jdt_ref += jdt_delta
        meteor_list[ref_ind].time_data -= tsec_delta


        meteor_list_tcorr = []

        for i, meteor in enumerate(meteor_list):

            # Only correct non-reference meteors
            if i != ref_ind:

                # Calculate the difference between the reference and the current meteor
                jdt_diff = meteor.jdt_ref - meteor_list[ref_ind].jdt_ref
                tsec_diff = jdt_diff*86400.0

                # Normalize all meteor times to the same reference time
                meteor.jdt_ref -= jdt_diff
                meteor.time_data += tsec_diff

            meteor_list_tcorr.append(meteor)

        ######

        # The reference JD for all meteors is thus the reference JD of the first meteor
        jdt_ref = meteor_list_tcorr[ref_ind].jdt_ref


        ### Precess observations from J2000 to the epoch of date
        meteor_list_epoch_of_date = []
        for meteor in meteor_list_tcorr:

            jdt_ref_vect = np.zeros_like(meteor.ra_data) + jdt_ref

            # Precess from J2000 to the epoch of date
            ra_prec, dec_prec = equatorialCoordPrecession_vect(J2000_JD.days, jdt_ref_vect, meteor.ra_data, 
                meteor.dec_data)

            meteor.ra_data = ra_prec
            meteor.dec_data = dec_prec

            # Convert preccesed Ra, Dec to altitude and azimuth
            meteor.azim_data, meteor.elev_data = raDec2AltAz_vect(meteor.ra_data, meteor.dec_data, jdt_ref,
                meteor.latitude, meteor.longitude)

            meteor_list_epoch_of_date.append(meteor)


        ######


        return jdt_ref, meteor_list_epoch_of_date

    else:
        return None, None



