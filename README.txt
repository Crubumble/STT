This programm will provide a first analyses of your crew for voyages.

You can select between Analyse your entire crew regarding the usage for voyages and the reached time
or to get a proper crew for a specific combination of primary and secondary attribute.
In order to work you have to fill the example.xls (or any other xls with the right format) with your crew.
Than start main.exe and it will guide you through.


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
    3.2 Improve algorithm by using dilemma steps
        Avoid: [14000, 8000, 2500, 4000, 2000, 2000] to something like [11000, 9500, ...]
	Done but not ready yet