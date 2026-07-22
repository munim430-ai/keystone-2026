# Keystone CEO Orchestrator — convenience targets
.PHONY: demo test board drafts clean serve

demo:            ## end-to-end demo on a fabricated student ($0, no keys)
	cd .. && python -m orchestrator.cli demo

test:            ## run the orchestrator test suite
	cd .. && python -m pytest orchestrator/tests -q

board:           ## show the pipeline board + survival banner
	cd .. && python -m orchestrator.cli board

drafts:          ## show the pending approval queue
	cd .. && python -m orchestrator.cli drafts

serve:           ## run the intake webhook (uvicorn)
	cd .. && uvicorn orchestrator.intake:app --host 127.0.0.1 --port 8090

clean:           ## remove the local board mirror + demo student
	rm -rf .local_board
	rm -rf ../audit-system/students/demo-fabricated-student
