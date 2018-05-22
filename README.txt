This programm will provide a first analyses of your crew for voyages.

You can select between Analyse your entire crew regarding the usage for voyages and the reached time
or to get a proper crew for a specific combination of primary and secondary attribute.
In order to work you have to fill the example.xls (or any other xls with the right format) with your crew.


Usage on desktop windows PC:
1. If you have install python3 than run main.py on the terminal (also valid for Linux of course)
2. If you do not have and want any experience with python run the exe file

Usage for smartphone:
1. Install any python interpreter (no learning apps)
2. Navigate to the folder where the main.py and others files are by using 
	cd <foldername>
	oriantation where you are can be achieved by using command dir or ls 
3. tip: python main.py
4. Most likely it will complain about not knowing pandas (or any other package)
5 install missing packages (pandas, openpyxl) by tipping:
	pip install <packagename>
6. repeat 3-5 until it works
7. programm should now run and explain the next steps

Example usage:
1. Install pydriod3
2. use terminal and the TAB symbol on the top to quickly navigate to your download folder
3. tip: python main.py 
4. Use pip install or the pip function of the programm (more stable) to install pandas opxenpyxl
5. repeat 3 and install xlrd if necessary
6. enjoy the program.



For programmers:

important functions:
    
1. AnalyseCrew() -  takes about a minute!
If you want to check your list of crew member select this function. It provides
an overview how often a char is used when all combinations of voyages are
analysed. Also suggest which crew can be further fused (together with the frequency and rank of the crew)


2. getVoyageCrew()
If you just want the present Crew for specific attributes

OPEN steps:
1. Fill crew table with more crew and the fuse stages
2. Improve anaylses by showing the impact of fusing a char
3. Improve sample function
    3.1 Code usage/style
    3.2 Improve algorithm by user intel