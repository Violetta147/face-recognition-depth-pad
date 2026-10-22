import numpy as np
import pytest

from deepface_pad.metrics import roc_auc
from deepface_pad.report_figures import FigureWriter, roc_points


def test_roc_preserves_tied_scores_and_ranking_auc():
    labels = np.array([0,0,1,1,1])
    scores = np.array([.2,.5,.5,.7,.9])
    fpr,tpr = roc_points(labels,scores)
    area = np.sum(np.diff(fpr)*(tpr[1:]+tpr[:-1])/2)
    assert area == pytest.approx(roc_auc(labels,scores))
    assert (fpr[0],tpr[0]) == (0,0) and (fpr[-1],tpr[-1]) == (1,1)


def test_export_keeps_physical_size_and_prohibits_accidental_overwrite(tmp_path):
    import matplotlib.pyplot as plt
    from PIL import Image
    writer = FigureWriter(tmp_path,dpi=100)
    fig,ax = plt.subplots(figsize=(4,3),layout="constrained")
    ax.plot([0,1],[0,1]); writer.save(fig,"example","Caption with units and provenance.")
    with Image.open(tmp_path / "png/example.png") as image:
        assert image.size == (400,300)
    assert (tmp_path / "pdf/example.pdf").is_file() and (tmp_path / "svg/example.svg").is_file()
    fig,ax = plt.subplots()
    with pytest.raises(FileExistsError): writer.save(fig,"example","Do not overwrite")
    plt.close(fig)
