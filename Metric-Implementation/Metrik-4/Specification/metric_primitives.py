"""
Black-box Primitives

Primitive building blocks for the S-1 similarity metric.

These functions wrap complex external logic (NLP, matrix matching, graph edit
distance) into atomic, contract-guarded interfaces.  Each primitive is fully
specified below so that an independent implementation can be written from the
docstring alone.

Dependency map
--------------

+-------------------+----------------------------------------------------------+
| Primitive         | External dependency                                       |
+===================+==========================================================+
| CosineSim         | NLTK  (wordnet, omw-1.4, stopwords, averaged_perceptron  |
|                   | tagger, punkt)                                           |
+-------------------+----------------------------------------------------------+
| greedyOptimalSum  | NumPy  (ndarray support) or plain Python list-of-lists  |
+-------------------+----------------------------------------------------------+
| gedNormalized     | NetworkX  (graph_edit_distance / optimize_graph_edit_   |
|                   | distance) or graph-tool                                   |
+-------------------+----------------------------------------------------------+
| clampToUnit       | Pure Python (math module)                                 |
+-------------------+----------------------------------------------------------+

WordNet setup (run once before CosineSim is used)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import nltk
    nltk.download('wordnet')
    nltk.download('omw-1.4')
    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('punkt')

Exported functions:
    CosineSim        – NLP string similarity via WordNet vectors.
    greedyOptimalSum – Greedy maximum-weight bipartite matching on a matrix.
    gedNormalized    – Normalised Graph Edit Distance between two tagged graphs.
    clampToUnit      – Hard-clamp a float to [0.0, 1.0].
"""

import icontract
import networkx as nx
from typing import List, Union
import numpy as np

from ..Testset.metric_invariants import isValidSimilarity


# ----------------------------------------------------------------------
# NLP primitive
# ----------------------------------------------------------------------
@icontract.require(lambda s1: isinstance(s1, str))
@icontract.require(lambda s2: isinstance(s2, str))
@icontract.ensure(lambda result: isValidSimilarity(result))
def CosineSim(s1: str, s2: str) -> float:
    r"""
    Compute the semantic cosine similarity between two strings.

    This function implements the full NLP pipeline that transforms raw
    identifiers (e.g. class names, attribute names, relationship labels)
    into comparable weighted WordNet vectors.  The pipeline is
    camelCase-aware and uses Wu-Palmer semantic similarity to build a
    vocabulary-filtered vector space.

    Algorithm
    ---------
    1. **camelCase-aware tokenisation**

       Split the input string into tokens by detecting uppercase boundaries:

       * ``getData``      → ``["get", "Data"]``
       * ``XMLParser``    → ``["XML", "Parser"]``
       * ``user_name``    → ``["user", "name"]``
       * ``parseURL``     → ``["parse", "URL"]``
       * Digits are treated as hard boundaries: ``item1Count`` → ``["item", "1", "Count"]``
       * Spaces and underscores are also split points.

    2. **Lowercase normalisation**

       Every token is converted to lower case **after** tokenisation so
       that ``Data`` and ``data`` are treated identically.

    3. **POS tagging** (Penn Treebank tagset)

       Each token is tagged with its part-of-speech using the Penn
       Treebank tagset.  This is required so that the lemmatiser can
       choose the correct dictionary form.

       Typical tag→WordNet mapping used internally:

       +----------------+------------------+
       | Penn Treebank  | WordNet POS      |
       +================+==================+
       | NN, NNS, …     | ``n`` (noun)     |
       +----------------+------------------+
       | VB, VBD, …     | ``v`` (verb)     |
       +----------------+------------------+
       | JJ, JJR, …     | ``a`` (adjective)|
       +----------------+------------------+
       | RB, RBR, …     | ``r`` (adverb)   |
       +----------------+------------------+

    4. **Stopword removal**

       Tokens that appear in the standard English stopword list
       (``nltk.corpus.stopwords``) are discarded.

    5. **Lemmatisation**

       Remaining tokens are reduced to their dictionary form using
       ``nltk.WordNetLemmatizer`` with the POS hint derived from step 3.

    6. **Semantic-vocabulary filtering**

       A unified vocabulary ``V`` is built from the union of lemmas in
       both strings.  A candidate lemma is added to ``V`` only if its
       maximum Wu-Palmer similarity to **every** lemma already in ``V``
       is below the threshold ``τ = 0.85``.

       This prevents near-synonyms (e.g. ``person`` and ``human``)
       from inflating the vector space.

    7. **Weighted vector construction**

       For each input string, build a real-valued vector of length
       ``|V|``.  The i-th entry is the **maximum Wu-Palmer similarity**
       between any token in that string and the i-th vocabulary word.

    8. **Cosine similarity**

       .. math::

           \text{sim}(s_1, s_2)
               = \frac{v_1 \cdot v_2}{\|v_1\| \times \|v_2\|}

       where :math:`v_1` and :math:`v_2` are the vectors from step 7.

    Args
    ----
    s1 : str
        First string (e.g. a class or attribute name).
    s2 : str
        Second string.

    Returns
    -------
    float
        A similarity score in the closed interval ``[0.0, 1.0]``.

    Raises
    ------
    icontract.ViolationError
        If either argument is not a ``str``, or if the result falls
        outside ``[0.0, 1.0]``.

    Notes
    -----
    * **Dependencies** – ``nltk.corpus.wordnet`` and its data files
      must be present (see module-level WordNet setup snippet).
    * **Empty strings** – ``CosineSim("", "")`` returns ``1.0`` (two
      empty identifiers are considered identical).  If exactly one
      argument is empty, the result is ``0.0``.
    * **Missing WordNet entries** – If a token is not found in WordNet,
      Wu-Palmer returns ``None``.  The pipeline falls back to exact
      string equality: ``1.0`` if the token strings are identical after
      lower-casing, otherwise ``0.0``.
    * **POS-tag accuracy** – The lemmatiser is significantly more
      accurate when POS tags are supplied.  Without them, verbs such as
      ``are`` are not reduced to ``be``.

    Examples
    --------
    >>> CosineSim("Person", "User")
    0.0            # semantically unrelated

    >>> CosineSim("UserName", "login_id")
    0.0            # token overlap is low after stopword removal

    >>> CosineSim("Person", "Human")
    0.8            # approximate – depends on WordNet topology

    >>> CosineSim("", "")
    1.0

    >>> CosineSim("name", "")
    0.0

    See Also
    --------
    nltk.WordNetLemmatizer, nltk.pos_tag, nltk.corpus.wordnet
    """
    ...


# ----------------------------------------------------------------------
# Matrix primitive
# ----------------------------------------------------------------------
@icontract.require(lambda M: isinstance(M, (list, np.ndarray)))
@icontract.require(
    lambda M: (
        len(M) > 0
        and all(len(row) == len(M[0]) for row in M)
    )
    if isinstance(M, list)
    else True
)
@icontract.require(
    lambda M: (
        M.ndim == 2
        and M.shape[0] > 0
        and M.shape[1] > 0
    )
    if isinstance(M, np.ndarray)
    else True
)
@icontract.ensure(lambda result: result >= 0.0)
def greedyOptimalSum(M: Union[List[List[float]], np.ndarray]) -> float:
    """
    Greedy maximum-weight bipartite matching on a similarity matrix.

    The algorithm repeatedly selects the globally largest entry in the
    matrix, adds it to a running total, and then zeros out the entire
    row and column so that no element can be selected twice.  This
    produces a one-to-one matching between rows and columns that
    maximises the sum in a greedy (not globally optimal) fashion.

    Algorithm
    ---------
    1. ``total = 0.0``
    2. ``M = copy(input_matrix)``  (so the original is unmodified)
    3. Repeat ``min(n_rows, n_cols)`` times:

       a. Find ``(x, y) = argmax(M)`` (the position of the largest
          remaining value).
       b. ``total += M[x, y]``.
       c. Zero row ``x`` and column ``y`` of ``M``.  This is the
          ``change_pivot`` operation: it removes the matched row and
          column from further consideration.

    4. Return ``total``.

    Helper: change_pivot(M, x, y)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    In-place operation that sets every entry in row ``x`` and every
    entry in column ``y`` to ``0.0``.

    .. code-block:: python

        M[x, :] = 0.0
        M[:, y] = 0.0

    Where this is used
    ^^^^^^^^^^^^^^^^^^
    * ``propSim`` – class-to-class matching (``cSim`` matrix)
    * ``relSim`` – relationship-to-relationship matching
      (``raSim``, ``rdSim``, ``rgSim`` matrices)
    * ``intraSim`` – intra-subgraph matching (``gedNormalized`` matrix)

    Args
    ----
    M : list[list[float]] or numpy.ndarray
        A non-empty 2-D numeric matrix.  Rows correspond to elements of
        set *A*, columns to elements of set *B*.  Entry ``M[i][j]`` is
        the pairwise similarity between element *i* and element *j*.
        Matrices may be rectangular; the number of iterations is
        ``min(rows, cols)``.

    Returns
    -------
    float
        The sum of the selected diagonal.  Always non-negative.

    Raises
    ------
    icontract.ViolationError
        If ``M`` is not a 2-D structure, is empty, or has ragged rows.

    Notes
    -----
    * **Greedy, not optimal** – This is the ``change_pivot`` routine
      from the paper's specification.  It is *not* the Hungarian
      algorithm; the result is a greedy approximation of the maximum
      bipartite matching sum.  It is used because it is fast (no
      polynomial-time LP solver required) and empirically produces
      near-optimal results on the small matrices typical of class
      diagrams.
    * **Complexity** – For a dense matrix with ``k = min(rows, cols)``,
      each iteration scans the full matrix: ``O(k · rows · cols)``.
      In practice, because class-diagram matrices are tiny
      (|classes| < 50), this is negligible.
    * **Idempotence on squares** – If ``M`` is square and diagonal,
      every entry off the diagonal is zero, so the algorithm simply
      sums the diagonal in arbitrary order and still returns the same
      trace.
    * **Symmetry not required** – The matrix does not need to be
      symmetric; ``greedyOptimalSum`` works on any rectangular matrix.

    Examples
    --------
    Square identity-like matrix (all diagonal ones):

    >>> M = [[1.0, 0.0],
    ...      [0.0, 1.0]]
    >>> greedyOptimalSum(M)
    2.0

    Rectangular matrix (3 rows, 2 columns):

    >>> M = [[0.9, 0.1],
    ...      [0.2, 0.8],
    ...      [0.3, 0.4]]
    >>> greedyOptimalSum(M)
    1.7   # selects 0.9 (row 0, col 0) then 0.8 (row 1, col 1)

    All-zeros matrix:

    >>> M = [[0.0, 0.0],
    ...      [0.0, 0.0]]
    >>> greedyOptimalSum(M)
    0.0

    See Also
    --------
    numpy.argmax, numpy.unravel_index
    """
    ...


# ----------------------------------------------------------------------
# Graph primitive
# ----------------------------------------------------------------------
@icontract.require(lambda g1, g2: isinstance(g1, nx.Graph) and isinstance(g2, nx.Graph))
@icontract.require(lambda g1: all('tag' in data for _, data in g1.nodes(data=True)))
@icontract.require(lambda g2: all('tag' in data for _, data in g2.nodes(data=True)))
@icontract.require(
    lambda g1, g2: (
        all('tag' in data for _, _, data in g1.edges(data=True))
        and all('tag' in data for _, _, data in g2.edges(data=True))
    )
)
@icontract.ensure(lambda result: isValidSimilarity(result))
def gedNormalized(
    g1: nx.Graph,
    g2: nx.Graph,
) -> float:
    r"""
    Normalised Graph Edit Distance (GED) between two tagged graphs.

    Graph Edit Distance measures how many atomic edit operations are
    required to transform one graph into another.  Only vertex/edge
    **type tags** are considered for matching; labels or other metadata
    are ignored.

    Algorithm
    ---------
    1. **Compute the raw edit cost**

       Call ``networkx.graph_edit_distance`` (exact) for small graphs,
       or ``networkx.optimize_graph_edit_distance`` (approximate) for
       larger graphs.  Both functions are configured with tag-equality
       callbacks:

       .. code-block:: python

           node_match = lambda a, b: a['tag'] == b['tag']
           edge_match = lambda a, b: a['tag'] == b['tag']

       For the approximate variant, the generator may be truncated
       after a fixed number of candidates (e.g. 100) and the minimum
       cost among the evaluated candidates is taken.

    2. **Compute the normalisation denominator**

       .. math::

           \text{size} = \max\left(
               |V(g_1)| + |E(g_1)|,
               |V(g_2)| + |E(g_2)|
           \right)

       where :math:`|V|` is the node count and :math:`|E|` is the edge
       count.

    3. **Normalise and convert to similarity**

       .. math::

           \text{result} =
           \begin{cases}
               1.0 & \text{if size} = 0 \\
               1.0 - \frac{\text{cost}}{\text{size}} & \text{otherwise}
           \end{cases}

    Edit-operation contract
    ^^^^^^^^^^^^^^^^^^^^^^^
    Every primitive edit operation has **unit cost = 1**:

    * **Substitution** – replace a vertex or edge with a different
      type tag.
    * **Insertion** – add a new vertex or edge to the graph.
    * **Deletion** – remove an existing vertex or edge.

    Two vertices (or edges) are considered equal iff their ``tag``
    attribute strings are identical.

    Args
    ----
    g1 : networkx.Graph
        First graph.  Must be a NetworkX graph whose nodes and edges all
        carry a ``tag`` attribute.
    g2 : networkx.Graph
        Second graph, same constraints.

    Returns
    -------
    float
        A similarity score in ``[0.0, 1.0]``.
        * ``1.0`` means the graphs are structurally identical (zero edit
          cost).
        * ``0.0`` means the graphs are maximally different.

    Raises
    ------
    icontract.ViolationError
        If either graph is not a NetworkX graph, or if any node/edge
        lacks the required ``tag`` attribute, or if the result falls
        outside ``[0.0, 1.0]``.
    networkx.NetworkXError
        Propagated from the underlying GED implementation if the
        graphs cannot be processed.

    Notes
    -----
    * **Exact vs. approximate** – For graphs with :math:`\lesssim 15`
      nodes the exact ``graph_edit_distance`` is feasible.  For larger
      UCGs the approximate ``optimize_graph_edit_distance`` should be
      used to avoid combinatorial blow-up.  The caller decides which
      API to invoke based on graph size.
    * **Normalisation choice** – The denominator is the **larger** graph's
      combined node+edge count (not the sum of both).  This guarantees
      that the result is bounded in ``[0.0, 1.0]`` and is independent
      of graph order (``gedNormalized(g1, g2) == gedNormalized(g2, g1)``).
    * **Floating-point guard** – The result is passed through
      ``clampToUnit`` at the end of the top-level metric to protect
      against tiny negative values caused by IEEE-754 rounding.
    * **Dependency** – Requires NetworkX (``networkx.algorithms.similarity``)
      or ``graph-tool`` as the GED back-end.

    Examples
    --------
    Identical single-node graphs:

    >>> import networkx as nx
    >>> g1 = nx.Graph()
    >>> g1.add_node("A", tag="vc")
    >>> g2 = g1.copy()
    >>> gedNormalized(g1, g2)
    1.0

    One empty, one non-empty graph:

    >>> g_empty = nx.Graph()
    >>> g_full = nx.Graph()
    >>> g_full.add_node("A", tag="vc")
    >>> gedNormalized(g_empty, g_full)
    0.0

    See Also
    --------
    networkx.algorithms.similarity.graph_edit_distance,
    networkx.algorithms.similarity.optimize_graph_edit_distance
    """
    ...


# ----------------------------------------------------------------------
# Utility primitive
# ----------------------------------------------------------------------
@icontract.require(lambda x: isinstance(x, (int, float)) and not isinstance(x, bool))
@icontract.ensure(lambda result: isValidSimilarity(result))
def clampToUnit(x: float) -> float:
    r"""
    Hard-clamp a real number to the closed unit interval ``[0.0, 1.0]``.

    This is the final guard in the metric pipeline.  It protects the
    result against tiny floating-point excursions outside ``[0, 1]``
    caused by IEEE-754 rounding during the weighted combination of
    semantic and structural scores.

    Formula
    -------
    .. math::

        \text{result} = \max\bigl(0.0, \; \min(1.0, \; \text{float}(x))\bigr)

    Where it is used
    ^^^^^^^^^^^^^^^^
    Called exactly once at the end of the top-level ``metric()``
    function, after the combined similarity has been computed:

    .. math::

        \text{result} = (1 - \rho) \times \text{sem} + \rho \times \text{struc}

    with :math:`\rho = 0.5` (equal weighting of semantic and structural
    components).

    Args
    ----
    x : int or float
        The raw score to clamp.  Booleans are explicitly rejected to
        avoid treating ``True`` as ``1.0``.

    Returns
    -------
    float
        The value of ``x`` constrained to ``[0.0, 1.0]``.
        * Values ``< 0.0`` → ``0.0``
        * Values ``> 1.0`` → ``1.0``
        * Values inside the interval → unchanged (modulo ``float()`` cast)

    Raises
    ------
    icontract.ViolationError
        If *x* is not a real number or if the result somehow falls
        outside ``[0.0, 1.0]``.

    Notes
    -----
    * **Booleans** – ``bool`` is a subclass of ``int`` in Python, so an
      explicit ``not isinstance(x, bool)`` guard is required.  This
      prevents ``True`` or ``False`` from leaking into similarity
      pipelines where a boolean would be semantically wrong.
    * **NaN handling** – ``float('nan')`` is neither ``< 0`` nor ``> 1``,
      so ``min(1.0, nan)`` returns ``nan`` and ``max(0.0, nan)`` also
      returns ``nan``.  The ``isValidSimilarity`` post-condition will
      therefore reject NaN inputs.  Callers should ensure inputs are
      finite before calling ``clampToUnit``.

    Examples
    --------
    >>> clampToUnit(0.7)
    0.7

    >>> clampToUnit(1.3)
    1.0

    >>> clampToUnit(-0.1)
    0.0

    >>> clampToUnit(0.9999999999999999)
    0.9999999999999999

    See Also
    --------
    min, max, isValidSimilarity
    """
    return max(0.0, min(1.0, float(x)))
