# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 15:05:09 2013

@author: stuart
"""
import os
import tempfile
import pathlib

import pytest
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

import sunpy
import sunpy.map
import sunpy.data.test


filepath = sunpy.data.test.rootdir
a_list_of_many = [os.fspath(f) for f in pathlib.Path(filepath, "EIT").glob("*")]
a_fname = a_list_of_many[0]

AIA_171_IMAGE = os.path.join(filepath, 'aia_171_level1.fits')
RHESSI_IMAGE = os.path.join(filepath, 'hsi_image_20101016_191218.fits')


#==============================================================================
# Map Factory Tests
#==============================================================================
class TestMap:
    def test_mapsequence(self):
        # Test making a MapSequence
        sequence = sunpy.map.Map(a_list_of_many, sequence=True)
        assert isinstance(sequence, sunpy.map.MapSequence)

    def test_composite(self):
        # Test making a CompositeMap
        comp = sunpy.map.Map(AIA_171_IMAGE, RHESSI_IMAGE, composite=True)
        assert isinstance(comp, sunpy.map.CompositeMap)

    def test_patterns(self):
        # Test different Map pattern matching

        # File name
        eitmap = sunpy.map.Map(a_fname)
        assert isinstance(eitmap, sunpy.map.GenericMap)

        # Directory
        directory = pathlib.Path(filepath, "EIT")
        maps = sunpy.map.Map(os.fspath(directory))
        assert isinstance(maps, list)
        assert ([isinstance(amap, sunpy.map.GenericMap) for amap in maps])
        # Test that returned maps are sorted
        files_sorted = sorted(list(directory.glob('*')))
        maps_sorted = [sunpy.map.Map(os.fspath(f)) for f in files_sorted]
        assert all([m.date == m_s.date for m, m_s in zip(maps, maps_sorted)])

        # Pathlib
        path = pathlib.Path(a_fname)
        eitmap = sunpy.map.Map(path)
        assert isinstance(eitmap, sunpy.map.GenericMap)
        maps = sunpy.map.Map(directory)
        assert isinstance(maps, list)
        assert ([isinstance(amap, sunpy.map.GenericMap) for amap in maps])

        # Glob
        pattern = os.path.join(filepath, "EIT", "*")
        maps = sunpy.map.Map(pattern)
        assert isinstance(maps, list)
        assert ([isinstance(amap, sunpy.map.GenericMap) for amap in maps])
        # Test that returned maps are sorted
        files_sorted = sorted(list(pathlib.Path(pattern).parent.glob('*')))
        maps_sorted = [sunpy.map.Map(os.fspath(f)) for f in files_sorted]
        assert all([m.date == m_s.date for m, m_s in zip(maps, maps_sorted)])
        # Single character wildcard (?)
        pattern = os.path.join(filepath, "EIT", "efz20040301.0?0010_s.fits")
        maps = sunpy.map.Map(pattern)
        assert isinstance(maps, list)
        assert len(maps) == 7
        assert ([isinstance(amap, sunpy.map.GenericMap) for amap in maps])
        # Character ranges
        pattern = os.path.join(filepath, "EIT", "efz20040301.0[2-6]0010_s.fits")
        maps = sunpy.map.Map(pattern)
        assert isinstance(maps, list)
        assert len(maps) == 4
        assert ([isinstance(amap, sunpy.map.GenericMap) for amap in maps])

        # Already a Map
        amap = sunpy.map.Map(maps[0])
        assert isinstance(amap, sunpy.map.GenericMap)

        # A list of filenames
        maps = sunpy.map.Map(a_list_of_many)
        assert isinstance(maps, list)
        assert ([isinstance(amap, sunpy.map.GenericMap) for amap in maps])

        # Data-header pair in a tuple
        pair_map = sunpy.map.Map((amap.data, amap.meta))
        assert isinstance(pair_map, sunpy.map.GenericMap)

        # Data-header pair not in a tuple
        pair_map = sunpy.map.Map(amap.data, amap.meta)
        assert isinstance(pair_map, sunpy.map.GenericMap)

        # Data-wcs object pair in tuple
        pair_map = sunpy.map.Map((amap.data, WCS(AIA_171_IMAGE)))
        assert isinstance(pair_map, sunpy.map.GenericMap)

        # Data-wcs object pair not in a tuple
        pair_map = sunpy.map.Map(amap.data, WCS(AIA_171_IMAGE))
        assert isinstance(pair_map, sunpy.map.GenericMap)

        # Data-header from FITS
        with fits.open(a_fname) as hdul:
            data = hdul[0].data
            header = hdul[0].header
        pair_map = sunpy.map.Map((data, header))
        assert isinstance(pair_map, sunpy.map.GenericMap)
        pair_map, pair_map = sunpy.map.Map(((data, header), (data, header)))
        assert isinstance(pair_map, sunpy.map.GenericMap)
        pair_map = sunpy.map.Map(data, header)
        assert isinstance(pair_map, sunpy.map.GenericMap)

        # Custom Map
        data = np.arange(0, 100).reshape(10, 10)
        header = {'cdelt1': 10, 'cdelt2': 10,
                  'telescop': 'sunpy',
                  'cunit1': 'arcsec', 'cunit2': 'arcsec'}
        pair_map = sunpy.map.Map(data, header)
        assert isinstance(pair_map, sunpy.map.GenericMap)

    # requires dask array to run properly
    def test_dask_array(self):
        dask_array = pytest.importorskip('dask.array')
        amap = sunpy.map.Map(AIA_171_IMAGE)
        da = dask_array.from_array(amap.data, chunks=(1, 1))
        pair_map = sunpy.map.Map(da, amap.meta)
        assert isinstance(pair_map, sunpy.map.GenericMap)

    # requires sqlalchemy to run properly
    def test_databaseentry(self):
        sqlalchemy = pytest.importorskip('sqlalchemy')
        sunpy_database = pytest.importorskip('sunpy.database')
        db = sunpy_database.Database(url='sqlite://', default_waveunit='angstrom')
        db.add_from_file(a_fname)
        res = db.get_entry_by_id(1)
        db_map = sunpy.map.Map(res)
        assert isinstance(db_map, sunpy.map.GenericMap)

    @pytest.mark.remote_data
    def test_url_pattern(self):
        # A URL
        amap = sunpy.map.Map("http://data.sunpy.org/sample-data/AIA20110319_105400_0171.fits")
        assert isinstance(amap, sunpy.map.GenericMap)

    def test_save(self):
        # Test save out
        eitmap = sunpy.map.Map(a_fname)
        afilename = tempfile.NamedTemporaryFile(suffix='fits').name
        eitmap.save(afilename, filetype='fits', overwrite=True)
        backin = sunpy.map.Map(afilename)
        assert isinstance(backin, sunpy.map.sources.EITMap)

#==============================================================================
# Sources Tests
#==============================================================================
    def test_sdo(self):
        # Test an AIAMap
        aia = sunpy.map.Map(AIA_171_IMAGE)
        assert isinstance(aia, sunpy.map.sources.AIAMap)
        # TODO: Test a HMIMap

    def test_soho(self):
        # Test EITMap, LASCOMap & MDIMap
        eit = sunpy.map.Map(os.path.join(filepath, "EIT", "efz20040301.000010_s.fits"))
        assert isinstance(eit, sunpy.map.sources.EITMap)

        lasco = sunpy.map.Map(os.path.join(filepath, "lasco_c2_25299383_s.fts"))
        assert isinstance(lasco, sunpy.map.sources.LASCOMap)

        mdi_c = sunpy.map.Map(os.path.join(filepath, "mdi_fd_Ic_6h_01d.5871.0000_s.fits"))
        assert isinstance(mdi_c, sunpy.map.sources.MDIMap)

        mdi_m = sunpy.map.Map(os.path.join(filepath, "mdi_fd_M_96m_01d.5874.0005_s.fits"))
        assert isinstance(mdi_m, sunpy.map.sources.MDIMap)

    def test_stereo(self):
        # Test EUVIMap & CORMap & HIMap
        euvi = sunpy.map.Map(os.path.join(filepath, "euvi_20090615_000900_n4euA_s.fts"))
        assert isinstance(euvi, sunpy.map.sources.EUVIMap)

        cor = sunpy.map.Map(os.path.join(filepath, "cor1_20090615_000500_s4c1A.fts"))
        assert isinstance(cor, sunpy.map.sources.CORMap)

        hi = sunpy.map.Map(os.path.join(filepath, "hi_20110910_114721_s7h2A.fts"))
        assert isinstance(hi, sunpy.map.sources.HIMap)

    def test_rhessi(self):
        # Test RHESSIMap
        rhessi = sunpy.map.Map(RHESSI_IMAGE)
        assert isinstance(rhessi, sunpy.map.sources.RHESSIMap)

    def test_sot(self):
        # Test SOTMap
        sot = sunpy.map.Map(os.path.join(filepath, "FGMG4_20110214_030443.7.fits"))
        assert isinstance(sot, sunpy.map.sources.SOTMap)

    def test_swap(self):
        # Test SWAPMap
        swap = sunpy.map.Map(os.path.join(filepath, "swap_lv1_20140606_000113.fits"))
        assert isinstance(swap, sunpy.map.sources.SWAPMap)

    def test_xrt(self):
        # Test XRTMap
        xrt = sunpy.map.Map(os.path.join(filepath, "HinodeXRT.fits"))
        assert isinstance(xrt, sunpy.map.sources.XRTMap)

    # TODO: Test SXTMap
