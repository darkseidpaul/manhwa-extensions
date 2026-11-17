# Adding or updating a source

1. Copy `src/en/<name>/` into a checkout of https://github.com/keiyoushi/extensions-source
2. Read that repo's `AGENTS.md` and `CONTRIBUTING.md` before editing — it is the
   source of truth and its conventions change.
3. Sources must extend `KeiSource` (never `HttpSource` directly).
4. `name`, `lang`, `id`, `baseUrl` are injected from the `source {}` block in
   `build.gradle.kts` — do not declare them in the class.
5. DTOs must be plain `class` (not `data class`) and use `@SerialName` only when
   the JSON key differs from the property name.
6. Lint before committing: `./gradlew :src:en:<name>:lintRelease`
