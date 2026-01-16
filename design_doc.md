# Design doc/High level design decisions

Some of this has been copied from ResearchRepo.

Note: "Tips and Code" shall refer to https://www.alignmentforum.org/posts/6P8GYb4AjtPXx6LLB/tips-and-code-for-empirical-research-workflows and "Apollo" shall refer to Apollo Research's Engineering Guide at https://docs.google.com/document/d/1LJedFJKrGs7vi-xA1ucQQxj_y85Z9x4lEmf4sFgeX6g/edit?tab=t.0

Q: (from 15 Jan 2026): What are some pros and cons of prototyping with Colab notebook on web URL itself?

A:     Pros: "very easy to get started" for simple prototyping.
        They provide the compute for you so can infer/train open source models almost right out of the box (using just vLLM, which is fairly lightweight), relatively fast using their GPUs compared to local CPUs.
        You can run things just by clicking buttons.
        You can run parts of a notebook flexibly or rerun things at your command, which is good for fast iteration when fast iteration is your priority.
    Cons: "very hard to keep going" for complex projects.
        Connecting notebooks to each other requires navigating the google folders between them, which seems to be far less popular than navigating folders in a local filesystem. In the near future, AI assistants might still be really challenged by this.
        The nonlinear nature of runs means colabs by themselves provide very little natural version control, in a way that requires substantial mental energy every time to add on (either by pushing to git, or creating and updating your own versioning system, etc).
        Importing the correct packages has to be done every time for every colab notebook, which introduces friction compared to .env files in local filesystems. Not to mention code-maintenance, where you have to update each individual file's imports itself!
        When it comes to debugging: colabs in the web URL itself are quite subpar on many fronts. If you want to "manually" debug things, a variables tracer does exist. But what about using AI assistants to debug? The AI assistant found in the web URL itself is underpowered in my experience, so I'd have to manually download and take the file itself to claude.ai or something, and manually provide context, which in my experience completely saps my willpower compared to AI assistants that "live in" IDEs. And what about using humans (like asking on slacks/discords) to debug? The idiosyncratic nature of colab runtimes -- a relative minority of users in the slacks/discords I've used -- means some epistemic uncertainty every time I ask a question about a bug there.
        When it comes to information organization: I've observed that in many github repos, a substantial amount of information is contained outside of the code files themselves -- in README files, yamls, etc. The atomized nature of web-URL Colabs within the google folders they sit in means even if you add READMEs, yamls, etc in the google folders, it'll be unintuitive (in a willpower-taxing way) to access them every time, compared to popping open a VSCode editor and/or github repo and seeing the contents of a README right there on the way to read/write a code file. This criticism also extends to how easily AI assistants can edit things in a complex codebase, namely, how much context you have to feed in manually.
    Additionally I endorse most of the pros and cons mentioned under the "Jupyter Notebooks" heading in the Apollo Research guide.

Q: What are some pros and cons of prototyping with Colab notebook on VSCode, using VSCode's Colab extension?

A:     It inherits a good deal of the pros and cons from the Colab-notebook-on-web-URL-itself.
    Relative pro compared to that: since the colab is being worked on within a VSCode environment, the colab can get access to the full suite of AI coding assistant tools VSCode provides, instead of having to go via the websites of the frontier labs themselves to use their AI assistants.
    Relative con compared to any non-colab system: As of November/December at least, when I tried it, this option doesn't actually allow the colab to access your local filesystem, the "natural" filesystem, even if the colab file is stored there! When I tried running %ls on any cell of such notebook using the plugin, I found it displayed the file system found on the google drive I was logged in to, rather than the file system where the actual colab lives! This may or may not be fixed now, but I foresee substantial problems with using this system for complex codebases, as one basically has to expend extra energy setting up package imports, etc.

Q: What are some pros and cons of prototyping with Jupyter notebook on VSCode, without Colab?

A:     Pros: I think Jupyter notebooks, even without VSCode, recommended by both Tips and Code and Apollo? I chose VSCode because of its popularity btw. I feel it is great for the speed needed for prototyping, but doesn't time out or require as tedious a spool-up process as Colab instances do. Also, since the notebook file lives on the local filesystem itself and can access it, we can take advantage of downstream efficiencies like easy package control and (somewhat) easy AI assistant use right from VSCode.
    Cons: similar as Colabs, which make it less of a good fit for "production" level code. Also if inferring/using open source models you have to provide a separate inference engine/inference service like together.ai, not needed in Colabs.

Q: What are some pros and cons of prototyping with just a simple .py file(s) and/or using the command line?

A:     Pros: avoids nonlinear structures of any ipynb-based files (to some extent, though this might not be the foremost consideration during prototyping anyways).
    Cons: .py files can't quite store images like .ipynb files can, and many processes in inspect and elsewhere generate images! And command line runs can't quite be saved (except by bash files and that might be laborious for some cases?)

Q: (from 15 Dec 2025): Why eventually leave ResearchRepo to possibly focus on only methods and classes, while putting new scripts to be run in separate github repos altogether (one repo for each overall project)? And just have each project repo use the tools in ResearchRepo via importing?

A: Two main reasons as of 15 Dec: first practical, second professional. Practically, I found it really quite hard importing a method I want used from src/eval_of_evals/rrs.py to a notebook in welfare_defacc_prototyping scripts, where I needed to use it. Professionally, in the future the different projects might need different permissions (as a result of different funder/stakeholder requirements, etc), and it just presents far cleaner to be able to share each project's repo independently of the other projects'. 

Q: Why not use google colab notebooks and their GPUs for inference? 

A: (Epistemic status: somewhat firm) Will elaborate later.

Q: Why use Together.ai for inference? (I'm not talking about training/tuning here)

A: (Epistemic status: firm but not totally firm.) It's directly recommended in Tips and Code. Also, around Dec 2, I tried colab and runpod (nearest competitors; runpod recommended in both Tips and Code and Apollo) but each had basic integration issues then. (Like runpod needing the logistical overhead of a remote machine, I think?) Plus, together.ai works just as well in a colab notebook vs non-colab jupyter notebook (vscode or otherwise) vs a python file. This has many advantages, one of which is to ease portability between prototyping and production code, which might require going from notebook to non-notebook environments.

Q: Why integrate inspect (for evals) with WandB, instead of just using inspect?

A: I consider WandB to be a modern, mature, and stable technology for the important needs of logging things for future use as frictionlessly as possible, as well as seeing all of one's work at a glance with low friction. It's also directly recommended in Tips and Code as well as Apollo. The natural way I do that is via the bridging package https://inspect-wandb.readthedocs.io/en/latest/index.html.

Q: Why use uv for package management, instead of just pip or other competitors?

A: Directly recommended in Tips and Code. Also a great deal of AI safety research packages' documentation (like that of Inspect Evals and Inspect-Wandb) use uv in their tutorials.

Q: Why use separate folders for scripts vs non-scripts? And why use separate folders for prototyping code vs production code?

A: Broadly justified by Tips and Code as well as Apollo, and talking to some research engineers in person. Both guides have a general spirit of "two modes of research engineering" I'd like to capture.
