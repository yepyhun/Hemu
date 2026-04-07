# Plan 7 Végrehajtás - Unified final execution spec

## 1. Purpose

Ez a dokumentum a `plan7.md`, `plan7kieg.md` és `plan7kiegkieg.md` egységes, végrehajtásra kész specifikációja.

Nem új terv.
Nem új research.
Nem új filozófia.

Hanem a három dokumentum átfedésmentes, egységesített változata, amelyben benne van minden olyan logika, szabály, batch-sorrend, gate és kill criterion, ami ténylegesen kell az új memory kernel elindításához és megépítéséhez.

Ez a dokumentum abból a felismerésből indul ki, hogy a korábbi irány ott csúszott szét, ahol a rendszer már nem egy tiszta memory kernel volt, hanem több jó részmegoldás, több repo-ötlet és több félig átfedő fallback összedrótozott keveréke. A cél ezért nem újabb integration layer vagy még több okos toldás, hanem egy kisebb, erősebb, új kanonikus mag, amely a régi rendszer legerősebb invariánsait megtartja, de a scaffoldingot, redundanciát és overlapet eldobja.

Röviden:
- masterpiece by compression, not union
- új primary kernel, nem újabb ráépített köztes réteg
- a legjobb részeket sűríteni kell, nem egymás mellé hagyni

Ez a dokumentum:

- nem talál ki új irányt
- nem hagy ki végrehajtás-kritikus elemet
- kijelöli a hard law-kat, strong hypothesiseket és open questionöket
- egyértelműen rögzíti a Batch 0, Batch 1 és későbbi batch-határokat
- végrehajtható, önmagában olvasható spec

---

## 2. Product scope contract

Ez a memory kernel valódi termékcélja.

Nem benchmark-maxing.
Nem paper-claim önmagában.
Nem belső architektúra-esztétika.

Hanem ez:

1. `second-brain first`
- a rendszer nagy mennyiségű betöltött tudást kezel
- nem csak chat-memóriát
- könyvek, jegyzetek, dokumentumok, személyes tudás és workspace-anyagok együtt kezelhetők

2. `agent-native memory kernel`
- a rendszer Hermes alá illeszkedik
- nem külön mellékrendszer
- a memory layer a runtime elsőrangú része

3. `accuracy first`
- prioritási sorrend:
- pontosság > token-spórolás > sebesség

4. `write slow, read fast`
- a drága intelligencia mehet write-time, async és background digestion módba
- a query-time legyen rövid, olcsó, célzott és stabil

5. `local-first by default`
- a primary persistencia lokális
- a primary embedding-index lokális
- a rendszer pénzt és privacy-t is spórol

6. `embedding-on, but not truth`
- a local embedding default derived index
- az embedding nem truth source
- a truth source strukturált, provenance-es, időzített állapot

7. `multilingual / locale-neutral`
- a core nem angol cue-listákon áll
- locale-specifikus cue csak adapterben élhet
- a tudás nem törhet szét nyelvenként külön truth-surface-ekre

8. `1k -> 5k book viability`
- a rendszer már 1k könyves állapotban is vállalható legyen
- 5k könyves skálára legyen hiteles út

9. `high-risk corpus policy`
- medical / legal anyagok támogatottak
- de nem ugyanazzal a laza policyval
- ezek strictebb evidence-, idő- és abstention-szabályt kapnak

10. `use-case domination over vanity SOTA`
- a cél nem a paper-elismerés önmagában
- a cél az, hogy a saját valós use case-en a régi utat egyértelműen verje

11. `anti-Frankenstein`
- kisebb, tisztább primary path
- kevesebb overlap
- kevesebb fallback mesh
- több replacement power
- az új kernel nem lehet a régi részmegoldások uniója
- minden rétegnek a kanonikus mag sűrítését kell szolgálnia, nem újabb scaffoldingot

12. `anti-endless-patching`
- bounded batch-ek
- redesign trigger
- deletion / demotion / replacement accounting
- aritmetikai complexity accounting

13. `tool-heavy continuity viability`
- stabil `tool_profile`
- minimális tool schema churn
- artifact-first rehydration
- prompt-cache stabilitás mint termékkövetelmény

Rule:

- ha egy döntés nem segíti ezt a scope-ot, nem ennek a kernelnek a döntése

---

## 3. Confidence model

Három kötelező bizalmi szint van:

### 3.1. `hard law`
- ha sérül, így nem szabad felépíteni a rendszert
- nem preferencia, hanem törvény

### 3.2. `strong hypothesis`
- elég erős architecturális fogadás ahhoz, hogy batch induljon rá
- de ha a proof gate-eknél elbukik, vissza kell venni

### 3.3. `open question`
- szándékosan nyitott
- nem csúszhat be csendben a primary pathba
- csak explicit döntéssel mozdulhat el

Rule:

- `hard law` alapján építünk
- `strong hypothesis` alapján bounded módon kísérletezünk
- `open question` alapján nem emelünk primary működési módot

---

## 4. Hard laws

### 4.1. Truth laws

1. A `raw archive` és a `canonical truth` külön réteg.
2. A replay continuity, nem truth source.
3. A structured truth store a primary truth layer.
4. Az embedding, graph, curated nézetek és más indexek derived state-ek.
5. Correction / supersession / invalidation first-class write esemény.
6. Provenance kötelező.
7. Validity kötelező.
8. Exact recallhoz verbatim evidence-hez vissza kell tudni lépni.
9. A gist nem evidence.
10. High-risk namespace-ben summary-only answer nem lehet primary mód.
11. Source-backed canonical memory nem dobható ki pusztán azért, mert régi; supersede, archive vagy validity-close megengedett.

### 4.2. Core laws

1. A core nyelvfüggetlen.
2. Locale-specifikus cue csak adapterben élhet.
3. Nem lehet második párhuzamos truth platform.
4. Nem lehet god object.
5. Nem lehet broad raw fallback a primary correctness pathban.
6. A delivery nem correctness engine.
7. A Hermes integráció vékony boundary legyen, ne mély fork.
8. A native memory csak bounded derived snapshot lehet.
9. A tool surface stabil profile-okból álljon.
10. Turn-level schema churn nem lehet primary continuity-mechanizmus.
11. A nagy tool output artifactként éljen, ne default prompt payloadként.
12. A rendszer tudjon explicit artifact rehydrate-ot, ne full replayből éljen.
13. Az új kernel nem lehet integration layer a régi, átfedő memory-megoldások fölött.
14. Egy feladatra nem maradhat több, félig primer megoldáscsalád csak azért, mert mindegyik részben működik.

### 4.3. Retrieval laws

1. Nincs univerzálisan legjobb retrieval paradigma.
2. Query family szerint route-olni kell.
3. A retrievalnek completeness-t is védenie kell, nem csak nearest-match-et.
4. Exact-source querynél source-first route kell.
5. High-risk querynél evidence-first route kell.
6. Compact answer csak akkor engedhető, ha a kernel belső groundingja megvan.
7. A semantic route candidate generator lehet, de nem írhatja felül a truth discipline-t.
8. Relation és multi-hop queryknél evidence-chain completeness kell.
9. Source-sensitive módokban verification step kötelező.

### 4.4. Product laws

1. Pontosság > token-spórolás > sebesség.
2. Ami új komponens nem vált ki régit, az gyanús.
3. Benchmark nem tervezési forrás, csak ellenőrzés.
4. Paid eval nem discovery eszköz.
5. A kernelnek valós életben kell működnie.
6. Ha a hiba nem fér bele az aktuális batch deklarált családjába, meg kell állni.
7. Ha egy batch nem tud mérhetően egyszerűsíteni, nem sikeres.
8. Tool-heavy flowknál a prompt-cache stabilitás elsőrangú termékkövetelmény.
9. Token-spórolás nem trade-elődhet el a pontosság rovására.
10. Medical/legal támogatás nem jelentheti azt, hogy a rendszer bizonyíték nélkül beszél.
11. A drága memóriaformálás nem query-time kritikus ösvényen fusson.
12. A cél új kanonikus mag, nem a meglévő részmegoldások egyre sűrűbb összehegesztése.
13. A jó régi elemeket kompresszálni kell a primary kernelbe, nem párhuzamosan életben tartani.

---

## 5. Memory planes, trust classes and namespaces

### 5.1. Memory planes

A rendszer nem egyetlen memory bucket.

#### A. `raw_archive`
- eredeti dokumentum
- eredeti beszélgetés
- eredeti artifact
- verbatim span / source pointer
- checksum / version / timestamp / namespace

Ez az evidence alap.

#### B. `canonical_truth`
A primary strukturált truth réteg.

Első körben:
- `entity`
- `event`
- `state`
- `measure`
- `source`

#### C. `derived_propositions`
Status:
- `strong hypothesis`

Ez explicit állításokat, definíciókat, szabályokat, kivételeket, author-claim jellegű egységeket tárolhat.
Nem primary truth platform.
Derived réteg.

#### D. `retrieval_indices`
Derived state:
- lexical / FTS
- local embedding index
- association edges
- curated compilations
- optional graph projection

#### E. `delivery_views`
Csak handoff nézetek:
- `final_compact`
- `supported_compact`
- `exploratory_full`
- `artifact_rehydrate`

### 5.2. Namespace classes

#### `personal / second-brain`
- személyes jegyzetek
- preferenciák
- saját döntések
- olvasmányok
- second-brain tudás

Policy:
- compact és supported mód engedett
- source-supported preferált, de nem mindig kötelező

#### `workspace / project`
- projektanyagok
- repo-context
- workflow memory
- döntések

Policy:
- compact és supported mód engedett
- provenance kötelező

#### `library / books`
- könyvek
- tanulmányok
- cikkek
- hosszú dokumentumok

Policy:
- source-supported az alap
- compact csak groundinggal

#### `high-risk / medical-legal`
- orvosi anyagok
- jogi anyagok
- szabályozási vagy érzékeny következtetések

Policy:
- compact-only tiltva
- exact-source vagy source-supported kötelező
- validity / version / contradiction marker kötelező
- agresszív abstention kötelező

---

## 6. Memory admission / promotion / forgetting contract

### 6.1. Core principle

Nem minden bekerülő inputból lesz tartós memória.
A raw archive mindent megőrizhet.
A canonical memory szelektív.

### 6.2. Memory states

1. `raw_archive`
- eredeti forrás
- nem feltétlenül struktúrálva

2. `candidate_extract`
- nyersből kiemelt lehetséges memory unit
- még nem biztos, hogy tartós memory lesz

3. `provisional_memory`
- átment az első minőségi kapun
- már kereshető és korlátozottan felhasználható
- még nem teljesen stabil canonical truth

4. `canonical_memory`
- source-hoz, identityhez és időhöz kötött, tartósan vállalható memóriaegység

5. `derived_memory`
- index, summary, relation, curated view, embedding, proposition candidate
- soha nem primary truth source

6. `superseded_memory`
- korábban érvényes volt, de újabb állapot felülírta

7. `archived_memory`
- már nem aktív, de audit / provenance célra őrzött

8. `rejected_extract`
- zajos, túl gyenge vagy nem hasznos extract

### 6.3. Admission classes

1. `ephemeral`
- pillanatnyi, alacsony értékű zaj
- default: nem promotálódik canonical memoryvá

2. `personal_preference`
- preferencia, szokás, ismétlődő viselkedési minta
- promóció lehetséges

3. `project_context`
- projekt-, task-, workflow- vagy repo-releváns tudás
- promóció lehetséges

4. `document_knowledge`
- könyvből, cikkből, dokumentumból származó tudás
- promóció lehetséges, source kötelező

5. `high_risk_knowledge`
- medical/legal/regulatory kritikus tudás
- szigorított promóció

6. `transient_execution`
- végrehajtási trace, tool-call mellékzaj, ideiglenes runtime adat
- default: raw archive only vagy rövid életű provisional

### 6.4. Promotion rules

`candidate_extract -> provisional_memory` csak akkor történhet meg, ha:
- van minimális source pointer
- a tartalom nem puszta zaj
- legalább egyértelműen megállapítható:
  - kihez kapcsolódik
  - miről szól
  - milyen időbeli horgonya van
- nincs triviális duplikátum ugyanabban a formában

`provisional_memory -> canonical_memory` csak akkor történhet meg, ha:
- identity stabilizálható
- source és provenance stabil
- temporal állapot elégséges
- nincs feloldatlan erős konfliktus
- retrieval-useful egységet alkot
- várhatóan újrahasználható később

### 6.5. Rejection rules

`candidate_extract -> rejected_extract`, ha:
- puszta filler / udvariassági zaj
- túl általános és nem retrieval-useful
- nincs érdemi entity / state / relation / source anchor
- túl bizonytalan
- túl zajos
- egyszeri tool-output mellékzörej
- broad summary, ami nem vezethető vissza elég jól

### 6.6. Forgetting and demotion rules

A rendszer jellemzően nem töröl, hanem demotál.

Lehetséges mozgások:
- `canonical_memory -> superseded_memory`
- `provisional_memory -> archived_memory`
- `derived_memory -> rebuild`
- `candidate_extract -> rejected_extract`

### 6.7. Mandatory maintenance loops

1. dedupe
2. merge proposal
3. conflict detection
4. supersession detection
5. stale provisional demotion
6. derived index rebuild
7. activation decay

---

## 7. Temporal / versioning contract

### 7.1. Principle

A second brainnek tudnia kell:
- mikor figyelt meg valamit
- mikor jött létre a forrás
- mikortól volt igaz
- meddig volt igaz
- mi váltotta fel
- mit kell jelenlegi állapotként érteni

### 7.2. Mandatory temporal fields

Minden canonical memory unit lehetőség szerint hordozza:
- `observed_at`
- `source_created_at`
- `effective_from`
- `effective_to`
- `recorded_at`
- `superseded_at`
- `invalidated_at`

### 7.3. Minimal bitemporal model

A kernel minimálisan két időtengelyt kezel:

1. `event/effectivity time`
- mikor volt igaz a világban

2. `system/record time`
- mikor tudta meg vagy rögzítette a rendszer

Ez minimális bitemporal modell.
Nem opcionális.

### 7.4. Versioning edges

Kötelező edge-családok:
- `supersedes`
- `corrects`
- `conflicts_with`
- `derived_from`

### 7.5. Query-time temporal semantics

1. `current_state`
- jelenleg legjobb tudott állapot

2. `as_of_time`
- adott időpillanatra érvényes állapot

3. `history_trace`
- változástörténet

4. `source_time`
- a forrásban szereplő időt követi, nem a rendszerbe írás idejét

### 7.6. High-risk temporal rule

Medical/legal tartalomnál:
- `effective_from` és `source_created_at` nélkül semmi nem lehet high-confidence
- ha nincs egyértelmű idő, minimum low-confidence supported válasz adható, vagy abstention

---

## 8. Canonical model and source segmentation

### 8.1. Canonical model status

Status:
- `strong hypothesis`

### 8.2. Canonical objects

1. `entity`
2. `event`
3. `state`
4. `measure`
5. `source`

### 8.3. Canonical edges

1. `about`
2. `participant`
3. `object_of`
4. `located_at`
5. `has_state`
6. `has_measure`
7. `supported_by`
8. `quotes`
9. `supersedes`
10. `corrects`
11. `contradicts`
12. `derived_from`

### 8.4. Primary operators

1. `recall`
2. `attribute`
3. `count`
4. `aggregate`
5. `compare`
6. `temporal`
7. `trace_source`
8. `explain_relation`

### 8.5. Source segmentation rule

Minden dokumentumból háromféle derived egység készüljön:

1. `retrieval_chunk`
- embedding / FTS számára
- kb. 800–1400 karakteres sáv

2. `source_span`
- exact evidence egység
- page / section / paragraph / quoted span pointer

3. `canonical_extract`
- entity / event / state / measure / source compile

A canonical store nem lehet chunk-store álruhában.

---

## 9. Query modes, evidence, abstention and answer contract

### 9.1. Query modes

#### `exact_source_required`
Akkor használjuk, ha:
- idézet kell
- dátum kell
- szám kell
- szabály kell
- medical/legal kérdés jön
- a user explicit forrást kér

Követelmény:
- source-first retrieval
- exact grounding
- ha nincs elég evidence, abstain

#### `source_supported`
Akkor használjuk, ha:
- a válasz tömör lehet
- de forrásra visszaköthető kell legyen
- factual answer kell, nem laza emlékezés

Követelmény:
- supported answer packet
- grounding refs kötelező

#### `compact_memory`
Akkor használjuk, ha:
- személyes / second-brain recall
- alacsonyabb kockázat
- gyors, olcsó handoff kell

Követelmény:
- belső grounding megvan
- a delivery nem találhat ki új truthot

### 9.2. Support tiers

1. `exact_source`
- konkrét source span / page / section / quote visszaadható

2. `source_supported`
- egyértelműen visszaköthető forrásokra, de nem szó szerinti idézet

3. `multi_source_supported`
- több forrásból összerakott grounded válasz

4. `inferred_supported`
- részben következtetett, de erős forrásalappal

5. `weak_support`
- candidate-level, nem vállalható erős factual answerként

High-risk namespace-ben `weak_support` nem adható végső válaszként.

### 9.3. Abstention triggers

Kötelező abstention, ha:
- nincs elég forrás
- feloldatlan konfliktus van
- az időlogika nem tiszta
- a válasz csak semantic közelségből sejthető
- high-risk témában nincs exact/source-supported grounding
- nem dönthető el, melyik a legfrissebb vagy releváns verzió
- relation/multi-hop chain nem teljes

### 9.4. Confidence dimensions

Nem egyetlen confidence score kell, hanem:
- `support_confidence`
- `temporal_confidence`
- `resolution_confidence`
- `identity_confidence`
- `risk_class`

### 9.5. Confidence tiers

1. `high`
2. `medium`
3. `low`
4. `abstain`

`high` csak akkor adható, ha:
- support erős
- temporal helyes
- identity stabil
- nincs nyitott konfliktus

### 9.6. Typed answer contract

Minden operator outputja:
- `answer_type`
- `operator`
- `query_mode`
- `canonical_value`
- `display_value`
- `grounding_refs`
- `confidence_tier`
- `abstain_reason`
- `risk_class`
- `support_level`

High-risk módhoz ajánlott bővítés:
- `valid_as_of`
- `superseded_by`
- `conflict_refs`

### 9.7. Delivery views

A delivery feladata:
- `final_compact`
- `supported_compact`
- `exploratory_full`
- `artifact_rehydrate`

Tiltott:
- a delivery újraírja a kernel truthot
- a delivery találja ki a hiányzó evidenciát
- a delivery defaultként nagy source-blobot tol vissza

---

## 10. Retrieval constitution and routing policy matrix

### 10.1. Route families

1. `lexical/source-first`
- exact-source querykhez
- high-risk querykhez
- span- és citation-heavy recallhoz

2. `semantic-first`
- personal recall
- topic-level second-brain recall
- paraphrastic keresés

3. `association/graph-assisted`
- relation
- multi-hop
- cross-document linking
- theme discovery

4. `curated_memory_view`
- gyors compact recall
- precompiled high-signal surface

### 10.2. Canonical query families

1. `exact_lookup`
2. `factual_supported`
3. `personal_recall`
4. `relation_multihop`
5. `update_resolution`
6. `high_risk_strict`
7. `exploratory_discovery`

### 10.3. Routing table

#### `exact_lookup`
- primary route:
  - lexical
  - source index
- secondary:
  - semantic candidate allowed
- verifier:
  - mandatory source verification
- output:
  - `exact_source` preferred
- abstain:
  - yes, if no precise evidence

#### `factual_supported`
- primary route:
  - curated + semantic
- secondary:
  - source verification
- output:
  - `source_supported`
- abstain:
  - if evidence too weak or conflicting

#### `personal_recall`
- primary route:
  - curated + semantic
- secondary:
  - source or provenance check when uncertain
- output:
  - `compact_memory` or `source_supported`
- abstain:
  - only if memory is too weak or contradictory

#### `relation_multihop`
- primary route:
  - semantic candidate pool
  - targeted association / graph expansion
- secondary:
  - evidence-chain verification
- output:
  - `multi_source_supported`
- abstain:
  - if the chain is incomplete

#### `update_resolution`
- primary route:
  - temporal filtered source + canonical state
- secondary:
  - supersession / correction walk
- output:
  - `source_supported` or `exact_source`
- abstain:
  - if currentness cannot be resolved

#### `high_risk_strict`
- primary route:
  - lexical/source-first
- secondary:
  - temporal validation
  - contradiction check
- output:
  - `exact_source` or `source_supported`
- abstain:
  - mandatory on weak evidence

#### `exploratory_discovery`
- primary route:
  - semantic + association + curated
- secondary:
  - optional source grounding bundle
- output:
  - `exploratory_full`
- abstain:
  - generally not mandatory, but confidence must be downgraded

### 10.4. Expansion limits

Default caps:
- association hops: `1`
- graph hops: `2`
- semantic candidate pool: bounded k
- high-risk: no uncontrolled graph-first expansion

### 10.5. Routing law

- a route-ot a query family választja
- nem benchmark-shape
- nem a legújabb retrieval technika önmagában

### 10.6. Completeness rule

Relation és multi-hop queryknél a cél nem sima top-k recall,
hanem elég evidence chain visszahozása a grounded answerhez.

Ha a chain nem teljes:
- confidence downgrade
- vagy abstention

---

## 11. Local embedding constitution

### 11.1. Hard direction

- local embedding ON by default
- derived indexként
- nem primary truth sourceként

### 11.2. Hard law model-szinten nem fix

Hard law csak az, hogy:
- local-first legyen
- derived index legyen
- cheap query-time accesset segítsen
- ne legyen primary truth source
- cserélhető komponens legyen

### 11.3. Default and challenger set

Default irány:
- Jina-v5-class retrieval embedder

Kötelező challengerek:
- `BAAI/bge-m3`
- `intfloat/multilingual-e5-large`

### 11.4. Selection gates

A modellválasztást ezekkel kell lezárni:
- multilingual recall
- HU/EN paraphrase stability
- relation-heavy retrieval
- long-document chunk recall
- ingest throughput
- 5070-class hardveren futtathatóság

---

## 12. Background digestion scheduler contract

### 12.1. Principle

A drága intelligencia főként nem query-time-on fut.
A kernel write-time és background digestion alapú.

### 12.2. Job classes

1. `extract_job`
2. `canonicalize_job`
3. `dedupe_merge_job`
4. `conflict_detection_job`
5. `supersession_job`
6. `embedding_job`
7. `association_job`
8. `curation_job`
9. `proposition_candidate_job`
10. `maintenance_decay_job`

### 12.3. Priority order

1. extract
2. canonicalize
3. conflict / supersession
4. dedupe / merge
5. embedding
6. curation
7. association
8. proposition_candidate
9. maintenance_decay

### 12.4. Scheduling modes

1. `ingest_immediate`
- input után az első minimálisan szükséges lépések

2. `background_continuous`
- alacsony prioritású folyamatos emésztés

3. `nightly_deep`
- drágább, mélyebb consolidation és maintenance

### 12.5. Budget rules

Minden cycle-ra kell:
- max jobs
- max wall time
- max llm cost
- max embedding cost
- retry limit
- backoff policy

### 12.6. Query-time protection rule

Background digestion soha nem ronthatja:
- a query-time latency envelope-et
- a prompt-cache stabilitást
- a local-first működést

### 12.7. Background hard boundary

Background lehet:
- lassú
- költségérzékeny
- többfázisú

De nem lehet:
- truth-ot kitaláló fekete doboz
- ellenőrizetlen summary factory

---

## 13. Multilingual canonicalization / duplicate policy

### 13.1. Language-neutral identity rule

Minden stabil entity / concept / source lineage lehetőség szerint kap:
- `canonical_id`
- nyelvfüggetlen identity anchor

Ehhez tartozhatnak:
- `aliases`
- `surface_forms`
- `language_tags`
- `transliterations`

### 13.2. Duplicate classes

1. `exact_duplicate`
2. `paraphrase_duplicate`
3. `translation_duplicate`
4. `near_duplicate`
5. `conflicting_variant`

### 13.3. Merge rules

Merge csak akkor történhet, ha:
- identity elég stabil
- nincs jelentős meaning drift
- temporal eltérés kezelhető
- source lineage nem vész el

Különben:
- linkelés történik
- nem merge

### 13.4. Cross-lingual retrieval rule

A query nyelve nem korlátozhatja a recallt.
A rendszer:
- kereshet a query nyelvén
- de megtalálhat más nyelvű source-ot is
- a final answernek jeleznie kell, ha a support más nyelvű forrásból jött

---

## 14. Proposition / claim layer

### 14.1. Status

- `strong hypothesis`
- nem hard law az első batchben
- explicit future path

### 14.2. Trigger conditions

A proposition layer akkor nyitható meg, ha legalább kettő igaz:

1. relation/multi-hop queryk túl sok raw/source passt igényelnek
2. compare/temporal queryk túl gyakran esnek szét canonical-object-only módban
3. legal/medical rule-like tudás proposition nélkül túl gyenge pontosságot mutat
4. same-topic book knowledge túl sok laza snippetre esik szét
5. evidence-chain completeness proposition-szintű köztes reprezentáció nélkül gyakran hiányzik

### 14.3. Minimal proposition design

- `claim_id`
- `claim_text`
- `subject`
- `predicate`
- `object_or_value`
- `modality`
- `source_refs`
- `effective_time`
- `confidence`
- `status`

Status:
- derived
- never primary truth platform on its own

---

## 15. Hard boundaries by phase

### 15.1. Write-time

Write-time feladata:
- raw archive capture
- source segmentation
- canonical object compile
- provenance attach
- correction / supersession attach
- truth persist
- lexical index update
- embedding job queue
- consolidation job queue

### 15.2. Query-time

Query-time feladata:
- query family felismerés
- query mode kiválasztás
- route plan kiválasztás
- candidate retrieve
- operator execute
- typed answer emit

Tiltott:
- broad transcript replay mint default
- wide raw fallback mint primary correctness path
- query-time heavy re-mining ott, ahol write-time object lehet

### 15.3. Delivery-time

Delivery feladata:
- compact / supported / exploratory handoff
- artifact rehydrate

Tiltott:
- kernel truth újraírása
- evidenciák kitalálása
- nagy source-blob visszanyomása defaultként

---

## 16. Token budget contract

### 16.1. Mandatory answer modes

1. `compact_memory`
2. `source_supported`
3. `exact_source`
4. `exploratory_full`

### 16.2. Token targets

#### `compact_memory`
- rövid recallnál: minimum `60%` token saving a replay-heavy baseline-hez képest
- hosszú synthesisnél: target `90%+`

#### `source_supported`
- rövid factual kérdéseknél: minimum `50%` saving
- hosszabb supported answernél: target `70-85%`

#### `exact_source`
- nincs fix agresszív spórolási kényszer
- accuracy és source fidelity elsődleges

#### `exploratory_full`
- token budget nem lehet korlátlan
- de nem compactness az első cél

### 16.3. Retrieval caps

Mode-onként rögzíteni kell:
- max retrieved items
- max grounding refs
- max source spans
- max handoff chars/tokens

### 16.4. Hard rule

Ha a token saving úgy jön ki, hogy romlik a support precision vagy abstention precision, az nem nyereség.

---

## 17. Anti-loop execution protocol

### 17.1. Batch discipline

Minden batch előtt kötelező:
- pontos scope
- explicit `keep / cut / rebuild` cél
- explicit modules-to-replace lista
- explicit non-goals
- explicit proof obligations
- explicit replacement ledger
- explicit deletion / demotion ledger
- explicit arithmetic complexity ledger
- explicit query families impacted lista

### 17.2. No exploratory coding

Tilos:
1. azért kódolni, hogy majd a fizetős eval megmondja a következő hibát
2. open questionre primary pathot húzni
3. benchmark-shape fixet primary megoldásként bevinni
4. olyan új réteget hozzáadni, amelynek nincs azonnali replacement célja
5. high-risk policyt fellazítani jobb token-számért

### 17.3. Paid eval rule

Paid eval csak akkor nyitható, ha:
- a lokális gate-ek zöldek
- a deklarált replacement megtörtént
- nincs új broad fallback a primary pathban
- a deletion/demotion ledger lezár legalább egy régi primary útvonalat
- a tool surface stabil profile-ból működik
- a query modes ténylegesen elkülönülnek

### 17.4. Correction-round cap

Egy batchre maximum:
- `1` első implementációs kör
- `2` korrekciós kör

Ha ezután új shared family bukik ki, nem újabb patch jön, hanem tervrevízió.

### 17.5. Redesign trigger

Azonnali stop kell, ha:
1. a hiba nem fér bele az aktuális batch deklarált családjába
2. a fix nem vált ki régit, csak új réteget rak mellé
3. a fix locale-specifikus cue-ra vagy benchmark-shape-re épülne
4. a fix a deliveryt használná correctness-engineként
5. a fix high-risk queryket compact-only irányba tolná
6. a fix a prompt-cache stabilitást rontaná
7. a batch végén nincs valós complexity shrink
8. a fix eredménye több, egymással átfedő primer vagy fél-primer útvonal együttélése lenne
9. a javítás ténylegesen csak tinkering, nem kanonikus egyszerűsítés

### 17.6. Replacement / deletion accounting

Minden batch végén kötelező kimondani:
- mi lett az új primary út
- mely régi primary út szűnt meg
- mely modul lett demotálva
- mely modul marad csak debug / compatibility / explicit fallback szerepben
- hány primary path lett kevesebb
- hány fallback lett kevesebb
- mennyivel csökkent a prompt surface
- mennyivel csökkent a query-time branch count
- mennyivel változott a p95 latency
- mennyivel változott a token handoff
- mennyivel változott a high-risk answer precision
- modules deleted count
- modules demoted count

Ha nincs aritmetikai complexity shrink, a batch nem sikeres.

---

## 18. Gates, proof ladder and claim standard

### 18.1. Architecture proof

Bizonyítani kell, hogy:
- a batch hard law-kompatibilis
- a batch primary pathot egyszerűsít
- a batch replacement powerrel bír
- a batch nem növeli a párhuzamos truth surface-ek számát

### 18.2. Local proof

Bizonyítani kell, hogy:
- a typed answer object létrejön
- a régi primary path demotálódik
- a lokális suite zöld
- a tool-heavy flow nem nő vissza full-schema/full-output promptolás felé

### 18.3. 1k corpus proof

Bizonyítani kell, hogy:
- a rendszer 1k könyv / nagy dokumentum nagyságrendű állapotban is működik
- a retrieval quality nem omlik össze zajos nagy corpusszal
- a kernel-local rész nem válik domináns késleltetési forrássá
- a compact route továbbra is olcsó marad

### 18.4. 5k viability proof

Bizonyítani kell, hogy:
- van hiteles út 5k könyves állapot felé
- a derived index-stratégia fenntartható
- a source-first route nem válik használhatatlanná
- a proposition layer szükségességéről adatvezérelt döntés születik
- nincs catastrophic retrieval collapse
- nincs uncontrolled latency explosion
- nincs truth-surface fragmentation by language

### 18.5. Latency envelope proof

Bizonyítani kell, hogy:
- simple recall p95 a cél envelope-ben van
- supported answer p95 a cél envelope-ben van
- a high-risk route nem kényszeríti vissza a teljes replayt
- a kernel-local idő külön mérve is vállalható

### 18.6. Token proof

Bizonyítani kell, hogy:
- compact mode rövid recallnál erős tokennyereséget ad
- hosszú synthesisnél a compact/supported út drasztikusan kevesebb handoff tokent kér
- source-supported módnál a grounding nem szakad szét
- exact-source módnál a pontosságot nem áldozzuk be tokenért

### 18.7. High-risk proof

Bizonyítani kell, hogy:
- medical/legal namespace-ben az evidence discipline ténylegesen erősebb
- az abstention működik
- az update / correction / supersession jól érvényesül
- a rendszer nem válaszol magabiztosan gyenge source-tal

### 18.8. Product proof

Bizonyítani kell, hogy:
- a correctness nem romlik
- a token-hatékonyság javul
- a latency nem kényszerít broad fallbackre
- a production-szerű end-to-end használatnak hiteles útja van
- a rendszer a saját use case-en jobban teljesít, mint a régi út

### 18.9. Use-case domination standard

A rendszer akkor sikeres, ha a saját valós use case-en dominálja a régi megközelítést.

Ehhez teljesülnie kell:
1. a saját hard law-jait tartja
2. a primary path kisebb és tisztább lett
3. valódi régi primary rétegeket váltott ki
4. a second-brain recall pontossága erős maradt
5. a token-spórolás nem trade-elődött el a pontosság rovására
6. az 1k corpus proof zöld
7. az 5k viability út hiteles
8. a high-risk policy nem csak deklaráció
9. a query-time gyors, stabil és routing-aware
10. a benchmark csak megerősíti azt, ami belsőleg már bizonyított

### 18.10. SOTA claim standard

A rendszer csak akkor nevezhető SOTA-közelinek vagy SOTA-nak, ha:
1. a saját hard law-jait tartja
2. a primary path ténylegesen kisebb és tisztább lett
3. a replacement/deletion accounting alapján valódi régi primary rétegeket kiváltott
4. a correctness production-szerű használatban erős maradt
5. a token-hatékonyság nem trade-elődött el a pontosság rovására
6. a sebességnek hiteles, nagy állapotra is vállalható útja van
7. a multilingual viselkedés nem cue-listás heurisztikákon áll
8. a benchmark-eredmény csak megerősíti azt, ami belsőleg már bizonyított

---

## 19. Evaluation gate sheet and benchmark protocol

### 19.1. Evaluation families

Minimum eval familyk:
1. `exact_lookup`
2. `factual_supported`
3. `personal_recall`
4. `relation_multihop`
5. `update_resolution`
6. `abstention`
7. `multilingual_parity`
8. `high_risk_strict`

### 19.2. Green thresholds for 1k corpus

#### Accuracy / support
- `exact_lookup` exactness: `>= 0.90`
- `factual_supported` correctness: `>= 0.85`
- `personal_recall` correctness: `>= 0.85`
- `relation_multihop` grounded correctness: `>= 0.75`
- `update_resolution` correctness: `>= 0.80`
- `abstention precision`: `>= 0.85`
- `high_risk support precision`: `>= 0.92`

#### Multilingual parity
- HU vs EN answer-quality delta: `<= 0.08`

#### Latency
- simple recall p95: `<= 5s`
- supported answer p95: `<= 10s`

#### Token
- compact mode short recall saving: `>= 60%`
- long synthesis compact saving: `>= 90%`

### 19.3. Viability thresholds for 5k corpus

Required:
- no catastrophic retrieval collapse
- no uncontrolled latency explosion
- no truth-surface fragmentation by language
- no high-risk collapse
- relation/multihop remains usable

Suggested thresholds:
- `exact_lookup >= 0.85`
- `factual_supported >= 0.80`
- `relation_multihop >= 0.68`
- `abstention precision >= 0.82`
- `high_risk support precision >= 0.90`
- simple recall p95 `<= 6s`
- supported answer p95 `<= 12s`
- red if architecture needs broad replay to achieve this

### 19.4. Red conditions

Azonnali piros, ha:
- high-risk queryknél confident weak-support answer jelenik meg
- multilingual miatt truth duplication uncontrolled
- update-resolution gyakran régi állapotot ad jelenként
- exact-source mód semantic guessre támaszkodik
- token saving broad truth lossból jön

### 19.5. External sanity gate

Külső sanity gate maradhat:
- LongMemEval
- conversational long-term memory coverage-re

### 19.6. Internal primary gate

A primary gate a saját use-case suite.

Corpus mix minimum:
- books
- notes
- project/workspace docs
- personal second-brain entries
- medical/legal strict slice

Query mix minimum:
- exact source
- summary-supported
- preference recall
- relation/multi-hop
- update/correction
- contradiction
- abstention
- multilingual paraphrase
- high-risk strict

### 19.7. Mandatory telemetry

Mérendő dimenziók:
1. query family
2. query mode
3. route plan
4. kernel-local latency
5. total latency
6. retrieved item count
7. grounding ref count
8. handoff prompt tokens
9. final answer tokens
10. abstain / supported / compact outcome

---

## 20. Implementation batches

### 20.1. Batch 0 - Foundation freeze

Nem feature-batch.
Hanem foundation-freeze batch.

Célja:
- schema and lifecycle freeze
- routing freeze
- answer contract freeze
- telemetry freeze
- evaluation harness freeze
- admission / promotion / forgetting contract freeze
- temporal / versioning contract freeze
- token budget contract freeze

Batch 0 csak akkor tekinthető késznek, ha dokumentumszinten befagyott:
1. admission / promotion / forgetting contract
2. temporal / versioning contract
3. routing matrix
4. evidence / abstention / confidence contract
5. token budget contract
6. eval gate sheet

### 20.2. Batch 1 - First implementation batch

Az első tényleges implementation batch.

Minimal scope:
- raw archive
- canonical truth minimal object set
- provisional / canonical lifecycle
- source segmentation
- shared object envelope
- 5 canonical object
- canonical edges
- `attribute`
- `count`
- `aggregate`
- typed answer contract
- query mode separation
- slim delivery
- stable tool-profile boundary
- local embedding default derived index bekötése
- source-first route szigorítása
- strict high-risk policy foundation
- telemetry and eval harness hooks

Non-goals:
- teljes replay újratervezés
- proposition-layer primaryvé tétele
- autoresearch loop
- `compare` / `temporal` full beemelése
- benchmark-specifikus special-case családok felvétele
- turn-level tool schema orchestration visszafújása
- a régi részmegoldások mechanikus uniója vagy egyben továbbhordása

Proof obligations:
- az `attribute / count / aggregate` primary út már nem broad executor
- a typed answer contract az elsődleges handoff
- a delivery nem írja újra a kernel truthot
- legalább egy jelentős régi primary surface demotálódik
- a local embedding derived indexként ténylegesen működik
- a source-first mód high-risk queryknél ténylegesen külön policy
- a replacement ledger és deletion ledger lezárható
- a batch eredménye kisebb, tisztább kanonikus mag, nem újabb integration layer

### 20.3. Batch 2 boundary - Expansion batch

Csak akkor nyitható, ha Batch 1 zöld.

Scope:
- `compare`
- `temporal`
- relation / association erősítés
- proposition candidate layer
- multilingual parity gates
- 1k corpus proof teljesítése

Open-question boundary:
- proposition layer csak akkor emelhető feljebb, ha az 5 object modell könyvskálán ténylegesen kevés
- graph-assisted route csak akkor mélyülhet, ha valódi completeness-nyereséget ad

---

## 21. Immediate cuts and demotions

Ezek nem maradhatnak primary correctness pathban:

1. generic raw-record fallback
2. broad general synthesis
3. overlapping compiled surface-háló
4. delivery mint answer-rewriter
5. query-time újrabányászás ott, ahol write-time object lehet
6. full tool schema újraküldés mint default continuity-mechanizmus
7. evidence nélküli confident compact answer high-risk namespace-ben
8. régi, félig átfedő memory-megoldások párhuzamos primer vagy fél-primer együttélése
9. olyan integration layer, amely csak összedrótozza a régi jó ötleteket új kanonikus mag helyett

Maradhatnak:
- debug
- compatibility
- explicit fallback

De nem lehetnek primaryek.

---

## 22. Open questions

### 22.1. Strong hypotheses

1. az 5 canonical object elég az első hasznos maghoz
2. a local embedding default derived indexként erős nyerő lesz
3. a sekély association / graph expansion elég az első hasznos multi-hop szinthez
4. a typed answer + slim delivery út kisebb primary pathot ad
5. a proposition layer későbbi derived rétegként fog kelleni, de nem első batchben

### 22.2. Open questions

1. Az 5 object pontosan elég-e hosszú távon.
2. A proposition / claim layer mikor válik szükségessé.
3. A 8 operator pontosan elég-e hosszú távon.
4. Kell-e mélyebb dual-route retrieval.
5. Mennyire kell explicit bitemporal modell első körben.
6. Milyen mély legyen az association/graph route első hasznos formája.
7. Melyik local embedding modell a legjobb trade-off a saját hardveren.

---

## 23. Kill criteria

Az irányt újra kell bírálni, ha:

1. az új mag nem csökkenti a primary correctness path bonyolultságát
2. az új komponensek nem váltanak ki régit
3. újra fallback-háló kezd nőni
4. újra benchmark-familyk szerint kezdünk javítani object/operator helyett
5. a delivery megint correctness-engineként viselkedik
6. a paid eval újra discovery eszközzé válik
7. a 1k / 5k skálairány nincs konkretizálva vagy nem javul
8. a local embedding truth-szerű szerepet kezd kapni
9. a high-risk policy fellazul
10. a token-spórolás oltárán a grounded precision romlik
11. az admission szabályok ellenére a rendszer memory dumpként viselkedik
12. a temporal/versioning modell nem képes stabil update-resolutionre
13. a router túl sok queryt ugyanarra a broad útra terel
14. az abstention policy papíron létezik, de gyakorlatban nem működik
15. a background digestion túlterheli a local-first használatot
16. a multilingual corpus truth-fragmentationt okoz
17. a proposition layer hiánya sorozatos reasoning-hiányt okoz, de nincs megnyitva trigger szerint
18. az 1k green gate nem teljesül
19. az 5k viability irány csak deklaráció marad
20. ugyanarra a feladatra több, egymást részben fedő primer vagy fél-primer megoldás marad életben tartva
21. a javítások ismét tinkering-loopba csúsznak, mert a rendszer kompresszió helyett újabb uniókat termel

---

## 24. Final operating rule

Innentől ez a memory kernel csak akkor tekinthető helyes iránynak, ha:

- pontosabb
- tokenhatékonyabb
- query-time gyorsabb
- write-time intelligensebb
- jobban kezeli az update-et és az időt
- jobban kezeli a multilingual corpust
- high-risk módban fegyelmezettebb
- kisebb primary correctness pathon működik
- jobban illeszkedik a valódi second-brain use case-hoz
- és bizonyíthatóan több régi primary mechanizmust vált ki, mint amennyit hozzáad
