# GitHub release checklist

배포 전 확인:

- [ ] `.venv/` 또는 Conda environment가 repo에 들어가지 않았는지 확인
- [ ] 기존 upstream `coin-ft/.git/` 같은 nested Git repository가 없는지 확인
- [ ] 개인 데이터 / 실험 CSV / credentials / absolute home path가 없는지 확인
- [ ] `python scripts/smoke_test.py` 통과
- [ ] AnySkin 실기기: `anyskin_viz <port>` 동작 확인
- [ ] CoinFT Left single: raw + visualization 확인
- [ ] CoinFT Right single: raw + visualization 확인
- [ ] CoinFT dual: independent FT232 두 개로 동시에 visualization 확인
- [ ] `/dev/serial/by-id/` 기준 Left/Right FTDI ID를 팀 내부 문서에 기록
- [ ] 각 CoinFT physical sensor와 calibration model/norm의 대응 확인
- [ ] CoinFT CC BY-NC-SA 4.0 및 Stanford의 commercial/sponsored-research 조건 검토
- [ ] README의 `<YOUR_GITHUB_REPO_URL>` placeholder를 실제 URL로 교체

권장 release tag:

```bash
git tag -a v1.0.0 -m "AnySkin + CoinFT runtime release"
git push origin v1.0.0
```
