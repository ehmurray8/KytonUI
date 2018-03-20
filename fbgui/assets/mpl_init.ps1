$site_packs = python -c "import sys; print([s for s in sys.path if 'site-packages' in s][0])"
cp kyton.mplstyle $site_packs\matplotlib\mpl-data\stylelib
cp play.gif $site_packs\matplotlib\mpl-data\images
cp pause.gif $site_packs\matplotlib\mpl-data\images
