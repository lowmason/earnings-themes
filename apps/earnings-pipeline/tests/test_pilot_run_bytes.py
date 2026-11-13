"""Byte pin for a pilot pass and a pilot run over invented text (plan 23, Task 1).

A performance change must write the same bytes. The test runs ``make_pass`` and
then ``make_run`` (replay, train) and compares the SHA-256 of every file under the
pass and run directories with a literal taken from the code before plan 23. The
pass does not depend on the calibration outcome, so one literal serves both cases.
"""

import importlib
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_themes.split import Partition

workflow = importlib.import_module("apps.earnings-pipeline.tests.test_pilot_workflow")

PASS_BYTES = {
    "alternative/attempts.parquet": "4396505e435e0c7b29b2c731dfde7ebbf31f390d35dca29ce985e9319bbdda83",
    "alternative/contexts.parquet": "0ecf2238eacadd6ab2d2eaa6b2f51bf59a62587bd0ccb106a981ede0b9b10522",
    "alternative/entailment.parquet": "32f3efc4f402bed541fc2d310769709772c13d4bda090e0fdaa7451cd3f3e64d",
    "alternative/evidence.parquet": "ffb472702b9773a65eb49773a0bbbd48bd557368455a13addd39f786b11119c0",
    "alternative/outcomes.parquet": "ca0ff13200f82681a00e20719dfe39660481fe2c63198f6367e72e6f2fa66b23",
    "alternative/run.json": "2ed8ab628363cc20895e4dea4afe0ddbd57ea0289fceaf6a2654054523655e3c",
    "alternative/targets.parquet": "8a54521c7a0df7f7178ca9205e0b1bc19c21eee53dbd67924e09d772702bdc3f",
    "alternative/trials.parquet": "783e8d7948d99d227e7a2bd23db82254794b52a337598644e66271b8ded218b6",
    "alternative/usage.parquet": "827d5235de5acec968b54e191fe360dc14e6efeecad603bc3a63fd1e115efa0d",
    "extraction/claims.parquet": "e0a2b7be234a8196e75b60491e324a0997a646b3f1c731fd8b6d71b6240c4642",
    "extraction/documents.parquet": "f573af635db9085429f44db9ffce09f5db5b34802bae558953ea6b2215ded7f1",
    "extraction/quotes.parquet": "ac0eae789c50ca360f8db6df4523f3f40648c06a198f512d50c73de0cfe9dd39",
    "extraction/rejections.parquet": "4e10c5ec974b80e2bfc5da08fa8e66958c815864b7156e22be817ba86b6cc653",
    "extraction/run.json": "665926f02d13567fd3204a1c23ada450d424a32e948fa00f24187e520ed384bf",
    "extraction/visits.parquet": "9006af571f07192acf8ad47361624537d674f6815c5fe972c8134e66460056b6",
    "extraction/windows.parquet": "6107a5b200c8b1d8d01fae20e606b79c833d1d24d699e36260d152d5778bab45",
    "pass.json": "93c3d1c5e36d2ab918a594c1fd2c4db83cae84f3b31574fc9f5a4b41db7b7a70",
    "proposals.json": "57025db05765dfd4a1fdf53536560d9f468b7a9368109eb3ca7369e73d5191b2",
    "support/attempts.parquet": "0c876abb55e7ab24f383add107eb2ac1454a64d0a6b1c30a57b02675a40842de",
    "support/contexts.parquet": "0ecf2238eacadd6ab2d2eaa6b2f51bf59a62587bd0ccb106a981ede0b9b10522",
    "support/entailment.parquet": "b00725c80204927dfb43e6fdf0953f73e40c66bc8eea64a50f1fc3ea87535c91",
    "support/evidence.parquet": "ffb472702b9773a65eb49773a0bbbd48bd557368455a13addd39f786b11119c0",
    "support/outcomes.parquet": "ca0ff13200f82681a00e20719dfe39660481fe2c63198f6367e72e6f2fa66b23",
    "support/run.json": "1ea4a29549e5ade700d9255abd0e277333eed88681880e11ab37e8fc6eebd829",
    "support/targets.parquet": "8a54521c7a0df7f7178ca9205e0b1bc19c21eee53dbd67924e09d772702bdc3f",
    "support/trials.parquet": "783e8d7948d99d227e7a2bd23db82254794b52a337598644e66271b8ded218b6",
    "support/usage.parquet": "d1ff2140d6ba485726ff56034b1a200b3f7be2ba7808ee423811d6081875f2f5",
}
RUN_BYTES = {
    "selected": {
        "analysis/assignment_claims.parquet": "6792564b93dc3cf504328e5864ddf6a06696e45addd9940a2a8c948f54744661",
        "analysis/claim_evidence.parquet": "faa17c9c94696c113d21ba38f54d0d3bde7a31f3d7bb607784ac03d3b6da4505",
        "analysis/claims.parquet": "a99c783f504622f729e5983e6d82e4f8da9df3481e666f0f189680a4361f2947",
        "analysis/classifications.parquet": "5e475a671841bd8c3fde93036d84370480a7a442a174f7776838624eba5acf2b",
        "analysis/completions.parquet": "2990a9371cdeee4ce717405888c2d10b6cac8ea86eaf61244b25d1d6e055f1db",
        "analysis/copies.parquet": "9a239e004060fdd63523d76639e351c9bfb05d1d1cea60f37eeaabdb43f8f0b1",
        "analysis/coverage.parquet": "22acc80fd89700c0b5f157d7e3ff5021b5fb924ab6bd5201ff6bb00a14ee52ae",
        "analysis/decisions.parquet": "ab0b9b9064adf033b88f05e333c4519ef6cec9460bd9172735cfcd74fc2abd40",
        "analysis/evidence.parquet": "6f154b503c8df1d0d647d76c5d3d22e364340a35944905f98f96cf2b26fc4892",
        "analysis/novelty.parquet": "331c375f420f21a3ec1524d898a8ce96a1895715cf8e35ee83414a978993641a",
        "analysis/observations.parquet": "4f0a884101baa0e59c75cf6da3abb65084cad11583ab1e33e5b9d96ee1bca571",
        "analysis/prevalence.parquet": "46cc9e58a31fd8946561cca01f51f32956ebeb968770d4822fcb2a972d6ffa4b",
        "analysis/quotes.parquet": "e6323b3d5bba2e92c98f77a1bcd875292720f45ec6ca3a0d426adf27752b7303",
        "analysis/rejections.parquet": "4e90cf8cb946ccec726d6498d44668555ecabf3ec8c0fbd52488ec947ec85af7",
        "analysis/run.json": "621be8fc20a704175b77249c1ee1b3631e337ed3bc8434ed35174c728769c8af",
        "coding/assignment_claims.parquet": "6792564b93dc3cf504328e5864ddf6a06696e45addd9940a2a8c948f54744661",
        "coding/assignments.parquet": "47d80c822770d56da8761b25eec2c212a7f950f04362cb88624bcfa6114bd83c",
        "coding/attempts.parquet": "1cd257a1a003810b2cf3281b7afa8ecfc33b934f233320dd8ea058ace340f030",
        "coding/attributes.parquet": "1d81b13a1ac46a8f99d01ea038e05b1069fca33d5ca6e097ff64a04625807f40",
        "coding/classifications.parquet": "83cdf2f6c585781fe45b7502be7591cb2811261596494a7e1df095786a5f9c73",
        "coding/decisions.parquet": "b6ae9361cbe48c1cebc8f5e4f69333433f286d5d8847ffc20300d5530e7c6802",
        "coding/novelty.parquet": "331c375f420f21a3ec1524d898a8ce96a1895715cf8e35ee83414a978993641a",
        "coding/proposals.parquet": "89ed9ae2ed0d7e71eeda985955c487fb208c77fef573c84842baae0b29f3a62b",
        "coding/run.json": "2faf754c3454753a10bbd1218f2c10365bd4347e5f7466a0b5cd87aceee5b2d1",
        "configuration.json": "7f794035fe9bc31cc1cba20a9a5fb536d081e820a835dab090e44d6d1f1a0c13",
        "receipt-33fa157bb9150e21a1f9ca7f696675c56dc56110a9605f7b2c915b0d71886dd5.json": "33fa157bb9150e21a1f9ca7f696675c56dc56110a9605f7b2c915b0d71886dd5",
        "report/artifacts/4cc5f1e0d9f41a118201b2b78ec176fdc34de6d43fbade8b4ffdf858f6ab6f34.source": "4cc5f1e0d9f41a118201b2b78ec176fdc34de6d43fbade8b4ffdf858f6ab6f34",
        "report/artifacts/b74eeaa1b24be43ac83b9c58de7df989183274c57677b1d6851ee3b3b0e2dae8.json": "b74eeaa1b24be43ac83b9c58de7df989183274c57677b1d6851ee3b3b0e2dae8",
        "report/artifacts/d586f1d3b9bdb09b08115b544e9dad6d97efcbe35eeb1a104e79f41e03fbd318.html": "d586f1d3b9bdb09b08115b544e9dad6d97efcbe35eeb1a104e79f41e03fbd318",
        "report/report.html": "0df92cf783544e84a9a16e32d21e52b07926c6a5d284ed8892b6d42fbc407174",
        "report/report.json": "d0d6a4160c26b0cb2d1eeaf25349b5bc00fca4b246a18150e59f1462037db34c",
        "run-record.json": "5a4efcf281605f499020c9cb7267119c2c257571d4429454cde7ca49c7e3a7ba",
        "support/attempts.parquet": "4396505e435e0c7b29b2c731dfde7ebbf31f390d35dca29ce985e9319bbdda83",
        "support/contexts.parquet": "0ecf2238eacadd6ab2d2eaa6b2f51bf59a62587bd0ccb106a981ede0b9b10522",
        "support/entailment.parquet": "32f3efc4f402bed541fc2d310769709772c13d4bda090e0fdaa7451cd3f3e64d",
        "support/evidence.parquet": "ffb472702b9773a65eb49773a0bbbd48bd557368455a13addd39f786b11119c0",
        "support/outcomes.parquet": "ca0ff13200f82681a00e20719dfe39660481fe2c63198f6367e72e6f2fa66b23",
        "support/run.json": "d8064baa1f2387e1009ac594bfcab2521f18ec65e147e8f1266b1b7f80b3f838",
        "support/targets.parquet": "8a54521c7a0df7f7178ca9205e0b1bc19c21eee53dbd67924e09d772702bdc3f",
        "support/trials.parquet": "783e8d7948d99d227e7a2bd23db82254794b52a337598644e66271b8ded218b6",
        "support/usage.parquet": "827d5235de5acec968b54e191fe360dc14e6efeecad603bc3a63fd1e115efa0d",
    },
    "none": {
        "analysis/assignment_claims.parquet": "8f56e4a5f9c70e0176764cd0321b87a56e87259ce19083a4476f3567711ae738",
        "analysis/claim_evidence.parquet": "faa17c9c94696c113d21ba38f54d0d3bde7a31f3d7bb607784ac03d3b6da4505",
        "analysis/claims.parquet": "a99c783f504622f729e5983e6d82e4f8da9df3481e666f0f189680a4361f2947",
        "analysis/classifications.parquet": "5e475a671841bd8c3fde93036d84370480a7a442a174f7776838624eba5acf2b",
        "analysis/completions.parquet": "1c734845ad8cf3f16f69b2dca08e79f994ca1b6171088ae5578793ad495b1de9",
        "analysis/copies.parquet": "9a239e004060fdd63523d76639e351c9bfb05d1d1cea60f37eeaabdb43f8f0b1",
        "analysis/coverage.parquet": "ffd4ce973b161b0e0073b2d6b67af0c9b55b506f01688bfd4518feea6ed9bae6",
        "analysis/decisions.parquet": "95246ed157a68281e6767eeaee3562e2c3b697e31b9e26bf48b5a0cd6bf2607c",
        "analysis/evidence.parquet": "6f154b503c8df1d0d647d76c5d3d22e364340a35944905f98f96cf2b26fc4892",
        "analysis/novelty.parquet": "331c375f420f21a3ec1524d898a8ce96a1895715cf8e35ee83414a978993641a",
        "analysis/observations.parquet": "0f5e83d7e835ccf9b839c178096f57607693a457b6a9dc220cc01c41df8630e5",
        "analysis/prevalence.parquet": "75012556773e2e77ad7027e0867e1711de654e7fb6057712eb663f9c85dff40f",
        "analysis/quotes.parquet": "e6323b3d5bba2e92c98f77a1bcd875292720f45ec6ca3a0d426adf27752b7303",
        "analysis/rejections.parquet": "4e90cf8cb946ccec726d6498d44668555ecabf3ec8c0fbd52488ec947ec85af7",
        "analysis/run.json": "73d1576892fc6f23f70c6af8f54df5a55b748cb1c73e83037c4dfc954f4d8c91",
        "coding/assignment_claims.parquet": "8f56e4a5f9c70e0176764cd0321b87a56e87259ce19083a4476f3567711ae738",
        "coding/assignments.parquet": "a81fcda3c0e91f19a8dac64695ae212b8a6080adde3734096025f163522060c9",
        "coding/attempts.parquet": "1cd257a1a003810b2cf3281b7afa8ecfc33b934f233320dd8ea058ace340f030",
        "coding/attributes.parquet": "1d81b13a1ac46a8f99d01ea038e05b1069fca33d5ca6e097ff64a04625807f40",
        "coding/classifications.parquet": "83cdf2f6c585781fe45b7502be7591cb2811261596494a7e1df095786a5f9c73",
        "coding/decisions.parquet": "0da14916ca88b2290fe5d1288bca8928eb2dd5b7630c11f3d479d2c57702238b",
        "coding/novelty.parquet": "331c375f420f21a3ec1524d898a8ce96a1895715cf8e35ee83414a978993641a",
        "coding/proposals.parquet": "89ed9ae2ed0d7e71eeda985955c487fb208c77fef573c84842baae0b29f3a62b",
        "coding/run.json": "0fa07f7a4ea2e123aaf58d139f6f419a7faa2e971c9051465452bdd36217bbb9",
        "configuration.json": "2ebcc214c077c8c7d49a0de3caa9511e4587a6b97dd1a289e4949c31c02e3756",
        "receipt-969b527ad00e2bb03b2a3cdba2bff227df339db94743106a2e92b6da721d5bf0.json": "969b527ad00e2bb03b2a3cdba2bff227df339db94743106a2e92b6da721d5bf0",
        "report/artifacts/4cc5f1e0d9f41a118201b2b78ec176fdc34de6d43fbade8b4ffdf858f6ab6f34.source": "4cc5f1e0d9f41a118201b2b78ec176fdc34de6d43fbade8b4ffdf858f6ab6f34",
        "report/artifacts/b74eeaa1b24be43ac83b9c58de7df989183274c57677b1d6851ee3b3b0e2dae8.json": "b74eeaa1b24be43ac83b9c58de7df989183274c57677b1d6851ee3b3b0e2dae8",
        "report/artifacts/d586f1d3b9bdb09b08115b544e9dad6d97efcbe35eeb1a104e79f41e03fbd318.html": "d586f1d3b9bdb09b08115b544e9dad6d97efcbe35eeb1a104e79f41e03fbd318",
        "report/report.html": "5c6cdba21a25fe6f0a05e99fb1dc209a94a7160a8eb1dd7832f84a4c4a7d45ee",
        "report/report.json": "7d9c24214a6bf0d533e50d613b75185d4b632669de960dced1de8d59f4293065",
        "run-record.json": "6630401442109c100c572c8ae3fc8f893c5265ceceed31c478e7c3a63d317046",
        "support/attempts.parquet": "4396505e435e0c7b29b2c731dfde7ebbf31f390d35dca29ce985e9319bbdda83",
        "support/contexts.parquet": "0ecf2238eacadd6ab2d2eaa6b2f51bf59a62587bd0ccb106a981ede0b9b10522",
        "support/entailment.parquet": "32f3efc4f402bed541fc2d310769709772c13d4bda090e0fdaa7451cd3f3e64d",
        "support/evidence.parquet": "ffb472702b9773a65eb49773a0bbbd48bd557368455a13addd39f786b11119c0",
        "support/outcomes.parquet": "ca0ff13200f82681a00e20719dfe39660481fe2c63198f6367e72e6f2fa66b23",
        "support/run.json": "d8064baa1f2387e1009ac594bfcab2521f18ec65e147e8f1266b1b7f80b3f838",
        "support/targets.parquet": "8a54521c7a0df7f7178ca9205e0b1bc19c21eee53dbd67924e09d772702bdc3f",
        "support/trials.parquet": "783e8d7948d99d227e7a2bd23db82254794b52a337598644e66271b8ded218b6",
        "support/usage.parquet": "827d5235de5acec968b54e191fe360dc14e6efeecad603bc3a63fd1e115efa0d",
    },
}


def file_hashes(directory: Path) -> dict[str, str]:
    return {
        path.relative_to(directory).as_posix(): sha256_hex(path.read_bytes())
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def now():
    return workflow.cases.NOW


@pytest.mark.parametrize(
    "none", [pytest.param(False, id="selected"), pytest.param(True, id="none")]
)
def test_pilot_run_writes_the_same_bytes(tmp_path, none):
    from earnings_pipeline.pilot_workflow import load_pass, make_pass, make_run

    config, _ = workflow.seed_case(tmp_path, seed=False, review=True)
    rt = workflow.runtime(config, [])
    pass_dir = tmp_path / "data/runs/pilot/train/pass"
    run_dir = tmp_path / "data/runs/pilot/train/run"
    passed = make_pass(
        config,
        rt,
        rt.scorer,
        partition=Partition.TRAIN,
        directory=pass_dir,
        fresh=None,
        support_ready=lambda: None,
        now=now,
    )
    loaded = load_pass(config, passed)
    artifact = workflow.bound_artifact(config, loaded, none=none)
    make_run(config, loaded, artifact, directory=run_dir, now=now)
    assert file_hashes(pass_dir) == PASS_BYTES
    assert file_hashes(run_dir) == RUN_BYTES["none" if none else "selected"]
