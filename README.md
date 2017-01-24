# CTRL-F

---

CTRL-F is a plugin for the PyMol molecular visualization software that enables users to search for amino acid sequences within PyMol objects and/or selections. The plugin can easily be called from anywhere within PyMol by pressing CTRL-F, just as to search for text in web browsers and many other applications.

### Installation

- CTRL-F requires PyMol versions 1.7.6.0 or above.
- CTRL-F is supported on UNIX/Linux and Windows (tested on Windows 7 and 8.1)

Get CTRL-F from the Github repository:

```sh
git clone https://github.com/fumarat/CTRL-F
```

Alternatively, download the repository as a zip file and install `CTRL_F.py` manually using the PyMol Plugin Manager.
As another alternative, you can use the PyMol "Install from PyMol wiki or any url" feature. Just paste the following url and click "fetch".

```sh
https://github.com/fumarat/CTRL-F/blob/master/CTRL_F.py
```

### Usage

- Bring the plugin up either from the Plugin menu or by pressing CTRL+F
- When only one PyMol object is present, the plugin will automatically select this object for searching
- If more objects and/or selections are present in PyMol, select the object/selection you want to search in
- By default, the plugin will be started in the **interactive** mode. This means you can just enter a search term in the respective field and if matching sequences have been found they will be highlighted automatically in PyMol. Also, a corresponding selection "interactive" will be saved in PyMol.
- If you turn off the **interactive** mode, you have to click **Find** or press **Enter** after entering a search term. In this case returned hits will be saved in PyMol as selections that are named after the object/selection and the search term that have been used for the search.
- To search in all available PyMol objects/selections at the same time, enable the **search all** mode. In this case, returned hits will be saved as "object/selection_all".
- The **search all** and **interactive** modes can also be combined.
- To delete all prior returned hits and the saved selections in PyMol press **Clear all hits**

Note that sometimes you have to manually switch back to the PyMol viewer window in order to see the updated "interactive" selection when using the **interactive** mode.

### Notes on using regular expression

Instead of providing a strictly alphanumeric search string (i.e. only one-letter code amino acids) you can also use regular expressions to search for various amino acid patters.

- \d for any single amino acid
- \d+ or .\* for a continuous stretch of any amino acids
- [] square brackets for selections of amino acids at a single position. For example the search SDF[GKLH]CCV will return a hit in the sequence AAASDFLCCV


### License

CTRL-F is licensed under the BSD-2-Clause license.


### Contributions

CTRL-F uses parts of **findseq** by Jason Vertrees, 2009, which is licensed under the BSD-2-Clause license.

If you want to contribute to CTRL-F, just fork it!
