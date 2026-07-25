# General Software Design Rules

## The following are from *The Pragmatic Programmer* book:

### Tip 11: DRY -- Don't Repeat Yourself.

*Every piece of knowledge must have a single, unambiguous, authoritative representation within a system.*

How Does Duplication Arise?
Most of the duplication we see falls into one of the following categories: 
- **Imposed duplication.** Developers feel they have no choice--the environment seems to require duplication.
- **Inadvertent duplication.** Developers don't realize that they are duplicating information.
- **Impatient duplication.** Developers get lazy and duplicate because it seems easier.
- **Interdeveloper duplication.** Multiple people on a team (or on different teams) duplicate a piece of information.

### Tip 12: Make It Easy to Reuse

What you're trying to do is foster an environment where it's easier to find and reuse existing stuff than to write it yourself...And if you fail to reuse, you risk duplicating knowledge.

## The following are from Chris Riccomini's and Dmitriy Ryaboy's *The Missing Readme: A Guide for the New Software Engineer*:

### Do's and Don'ts for Working with Code (p.44)

| DO'S | DON'TS |
|------|------|
| DO refactor incrementally. | DON'T overuse the phrase "technical debt." |
| DO keep refactoring commits separately from feature commits. | DON'T make methods or variables public for testing purposes. |
| DO keep changes small. | DON'T be a language snob. |
| DO leave code cleaner than you found it. | DON'T ignore your company's standards and tools. |
| DO use boring technology. | DON'T fork codebases without committing upstream. |

### Do's and Don'ts for Writing Operable Code (p. 73)

| DO'S | DON'TS |
|------|------|
| DO prefer compilation errors to run-time errors. | DON'T use exceptions for application logic. |
| DO make things immutable whenever possible. | DON'T use return codes for exception handling. |
| DO validate inputs and outputs. | DON'T catch exceptions that you can't handle. |
| DO study the OWASP Top 10 Web Application Security Risks. | DON'T write multiline logs. |
| DO use bug-checking tools and types or type hinting. | DON'T write secrets or sensitive data to logs. |
| DO clean up resources ater exceptions (especially sockets, file pointers, and memory). | DON'T manually edit configuration on a machine. |
| DO instrument your code with metrics. | DON'T store passwords or secrets in configuration files. |
| DO make your application configurable. | DON'T write custom configuration formats. |
| DO validate and log all configuration. | DON'T use dynamic configuration if you can avoid it. |

### Do's and Don'ts for Testing (p.107)

| DO'S | DON'TS |
|------|------|
| DO use tests to reproduce bugs. | DON'T ignore the cost of adding new testing tools. |
| DO use mocking tools to help write unit tests. | DON'T depend on others to write tests for you. |
| DO use code quality tools to verify coverage, formatting, and complexity. | DON'T write tests just to boost code coverage. |
| DO seed random number generators in tests. | DON'T depend solely on code coverage as a measure of quality. |
| DO close network sockets and file handles in tests. | DON'T use avoidable sleeps and time-outs in tests. |
| DO generate unique filepaths and database IDs in tests. | DON'T call remote systems in unit tests. |
| DO clean up leftover test state between test executions. | DON'T depend on test execution order. |


### Do's and Don'ts for Delivering Software (p.147)

| DO'S | DON'TS |
|------|------|
| DO use trunk-based development and continuous integration if possible. | DON'T publish unversioned packages. |
| DO use VCS (version control system) tools to manage branches. | DON'T package configuration, schema, images, and language packs together. |
| DO work with release and operations teams to create the right processes for your application. | DON'T blindly rely on release managers and operations teams. |
| DO publish release changelogs and release notes. | DON'T use VCSs to distribute software. |
| DO notify users when a release is published. | DON'T change release packages once they're published. |
| DO use off-the-shelf tooling to automate deployment. | DON'T roll out without monitoring the results. |
| DO roll changes out gradually with feature flags. | DON'T depend on deployment ordering. | 
| DO use circuit breakers to prevent applications from causing major damage. |  |
| DO use traffic shadowing and dark launches for major changes. |  |

### Do's and Don'ts for Creating Evolvable Architectures (p. 214)

| DO'S | DON'TS |
|------|------|
| DO remember YAGNI: "You Ain't Gonna Need It." | DON'T build too many abstractions without purpose. |
| DO use standard libraries and development patterns. | DON'T write methods with hidden ordering or argument requirements. |
| DO use an IDL to define your APIs. | DON'T surprise other developers with exotic code. |
| DO version external APIs and documentation. | DON'T make incompatible API changes. |
| DO isolate application databases from each other. | DON'T be dogmatic about internal API versioning. |
| DO define explicit schemas for all your data. | DON'T embed schemaless data in string or byte fields. |
| DO use migration tools to automate database schema management. |  |
| DO maintain schema compatibility if downstream consumers use your data. |  |

### "Understanding Complexity" (p. 194):

In *A Philosophy of Software Design* (Yaknyam Press, 2018), Stanford computer science professor John Ousterhout writes, "Complexity is anything related to the structure of a system that makes it hard to understand and modify the system." Per Ousterhout, complex systems have two characteristics: high *dependency* and high *obscurity*. We add a third: high *inertia*.

High *dependency* leads software to rely on otther code's API or behavior. Dependency is obviously unavoidable and eveen desirable, but a balance must be struck. Every new connection and assumption makes code harder to change. High-dependency systems are hard to modify because they have *tight coupling* and high *change amplification*. Tight coupling describes modules that depend heavily on one another. It leads to high change amplification, where a single change requires modifications in dependencies as well. Thoughtful API design and a restrained use of abstraction will minimize tight coupling and change amplification.

High *obscurity* makes it difficult for programmers to predict a change's side effects, how code behaves, and where changes need to be made. Obscure code takes longer to learn, and developers are more likely to inadvertently break things. *God objects* that "know" too much, global state that encourages side effects, excessive indirection that obscures code, and *action at a distance* that affects behavior in distant parts of the program are all symptoms of high obscurity. APIs with clear contracts and standard patterns reduce obscurity.

*Inertia*, the characteristic that we've added to Ousterhout's list, is software's tendency to stay in use. Easily discarded codde used for a quick experiment has low inertia. A service that powers a dozen business-critical applications has high inertia. Complexity's cost accrues over time, so high-inertia, high-change systems should be simplified, while low-inertia or low-change systems can be left complex (as long as you discard them or continue to leave them alone). 

Complexity cannot always be eliminated, but you can choose where to put it. Backward-compatible changes (discussed later) might make code simpler to use but more complicated to implement. Layers of indirection to decouple subsystems reduce dependency but increase obscurity. Be thoughtful about when, where, and how to manage complexity.

### "Design for Evolvability" (p. 195):

Faced with unknown future requirements, engineers usually choose one of two tactics: they try to guess what they'll need in the future, or they build abstractions as an escape hatch to make subsequent code changes easier. Don't play this game; both approaches lead to complexity. Keep things simple (known as KISS--*keep it simple, stupid*--thanks to the US Navy's penchant for acronyms and tough love). Use the KISS mnemonic to remember to build with simplicity in mind. Simple code lets you add complexity later, when the need becomes clear and the change becomes unavoidable.

### "Encapsulate Domain Knowledge" (p.199)

Software changes as business requirements change. Encapsulate domain knowledge by grouping software based on business domain--accounting, billing, shipping, and so on. Mapping software components to business domains will keep code changes focused and clean.

### "Evolvable APIs" (p. 200)

#### Keep APIs Small

#### Expose Well-Defined Service APIs

#### Keep API Changes 

#### Version APIs

### "Evolvable Data" (p. 205)

APIs are more ephemeral than persisted data; once the client and server APIs are upgraded, the work is done. Data must be evolved as applications change. Data evolution runs the gamut from simple schema changes such as adding or removing a column to rewriting records with new schemas, fixing corruption, rewriting to match new business logic, and massive migrations from one database to another.

Isolating databases and using explicit schemas will make data evolution more manageable. With an isolated database, you need only worry about the impact of a change on your own application. Schemas protect you from reading or writing malformed data, and automated schema migrations make schema changes predictable.

#### Isolate Databases

#### Use Schemas

#### Automate Schema Migrations

#### Maintain Schema Compatibility

## The following are from Cathy O'Neil and Rachel Schutt's *Doing Data Science: Straight Talk from the Frontline*:

### Care about how raw data treats values that are missing.

Do they replace the missing values with -1s? Or blank values? Or a specified "null" format, etc?

From Chapter 13.