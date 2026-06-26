Eine Halbordnung (oder partielle Ordnung) ist in der Mathematik eine binäre Relation auf einer Menge, die drei Axiome erfüllt: Reflexivität, Antisymmetrie und Transitivität. Im Gegensatz zur Totalordnung müssen nicht alle Elemente miteinander vergleichbar sein. Sie strukturiert Mengen, ohne zwingend eine lineare Reihenfolge vorzugeben.Hauptmerkmale und DefinitionEine Relation \(\le \) auf einer Menge \(M\) ist eine Halbordnung, wenn für alle \(a, b, c \in M\) gilt:Reflexivität: \(a \le a\) (jedes Element steht in Relation zu sich selbst).Antisymmetrie: Wenn \(a \le b\) und \(b \le a\), dann folgt \(a = b\).Transitivität: Wenn \(a \le b\) und \(b \le c\), dann folgt \(a \le c\).Beispiele und BegriffeTeilerrelation: Die Relation \(a\vert{}b\) (a teilt b) auf den natürlichen Zahlen ist eine Halbordnung.Inklusionsrelation: Die Teilmengenbeziehung \(\subseteq \) ist eine Halbordnung auf einem Mengensystem.Strenge Halbordnung: Eine Relation, die transitiv und asymmetrisch (irreflexiv) ist, z. B. die "echt kleiner" Relation (\(<\)).Totalordnung: Eine Halbordnung, bei der jedes Paar vergleichbar ist (z. B. \(\le \) auf reellen Zahlen).Wohlfundiertheit: Wenn in der Ordnung keine unendlich absteigenden Ketten existieren.

in tS-3:

In plain terms:
---
Partial Order (Halbordnung)
A relation ≤ on a set M is a partial order if it satisfies three axioms:
1. Reflexivity: a ≤ a
2. Antisymmetry: if a ≤ b and b ≤ a, then a = b
3. Transitivity: if a ≤ b and b ≤ c, then a ≤ c
The crucial one here is Antisymmetry. It means:
> If two elements are "as good as each other" in both directions, they must be the very same element.
Example: the subset relation ⊆ on sets.
- {1, 2} ⊆ {1, 2, 3} → true
- But {1, 2} ⊆ {2, 3} is false
- And {1, 2} ⊆ A and A ⊆ {1, 2} only if A = {1, 2}
---
Preorder (Quasiordnung)
A relation ≤ on a set M is a preorder if it satisfies only:
1. Reflexivity: a ≤ a
2. Transitivity: if a ≤ b and b ≤ c, then a ≤ c
It is missing Antisymmetry. This means:
> Two different elements can be "as good as each other" in both directions without being equal.
Example: score-based grading.
- Student A gets 75 points, Student B gets 75 points.
- A ≤ B (75 ≤ 75) and B ≤ A (75 ≤ 75).
- But A ≠ B (they are different people/models).
- So the relation is not antisymmetric.
This breaks the partial-order definition, but it is still a perfectly valid preorder.
---
The Key Difference
 	Partial Order	Preorder
Reflexive	yes	yes
Transitive	yes	yes
Antisymmetric	yes	no
If a ≤ b and b ≤ a	then a = b	then a ~ b (equivalent, but not necessarily identical)
---
Why This Matters for Metrik-1
The metric maps student models to a score. Two different UML models can easily happen to receive the exact same score. This means:
- The quality relation among models is a preorder, not a partial order.
- However, if we group models that share the same score into equivalence classes, and then look at the ordering between those classes, we get a true partial order on the quotient set.
So when tS-3-new.py tests "Antisymmetry", it is really testing: "If the metric assigns two different models the same score, is that assignment consistent?" — not: "Are different models always distinguishable?" (which would be false).
Does that distinction make sense for how you want to describe the metric in your work?

--> we test Preorder (Quasiordnung) which includes 
1. Reflexivity: a ≤ a
2. Transitivity: if a ≤ b and b ≤ c, then a ≤ c

It is missing Antisymmetry. This means:
> Two different elements can be "as good as each other" in both directions without being equal.

which makes sense in our case because ...

... which makes sense in our case because a grading metric evaluates "structural similarity to the reference", not the identity of the submission.
Two completely different UML models — e.g. one student renames class Person to Human, another student adds an extra attribute to Case — can both deviate from the instructor model by exactly the same amount. They are different models (a ≠ b), yet they are equally good according to the metric (q(a) = q(b), so a ≤ b and b ≤ a). 
This is not a bug; it is a feature of similarity-based grading. The metric does not claim every model is uniquely rankable. It only claims that no model should ever receive a worse score than a model that is objectively closer to the reference. A preorder captures exactly this intuition: it allows for equivalence classes of "equally similar" submissions while still enforcing a consistent ranking between them.