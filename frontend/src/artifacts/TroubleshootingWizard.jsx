import { useState } from 'react'

const DEFAULT_STEPS = [
  {
    question: 'Is shielding gas flowing correctly?',
    choices: ['Yes, flow looks normal', 'No, flow seems low or inconsistent'],
  },
  {
    question: 'Is the wire clean and dry?',
    choices: ['Yes', 'No or not sure'],
  },
  {
    question: 'Is the ground clamp connection solid?',
    choices: ['Yes', 'No'],
  },
  {
    question: 'Is travel speed controlled and steady?',
    choices: ['Yes', 'No'],
  },
]

export function TroubleshootingWizard({ data }) {
  const steps = data.steps ?? DEFAULT_STEPS
  const [index, setIndex] = useState(0)
  const [answers, setAnswers] = useState([])

  const step = steps[index]
  const complete = index >= steps.length

  return (
    <div className="artifact-body">
      {!complete ? (
        <>
          <div className="wizard-step">
            <p className="panel-label">Step {index + 1} of {steps.length}</p>
            <h4>{step.question}</h4>
          </div>
          <div className="choice-list">
            {step.choices.map(choice => (
              <button
                key={choice}
                className="choice-card"
                type="button"
                onClick={() => {
                  setAnswers(prev => [...prev, { question: step.question, choice }])
                  setIndex(prev => prev + 1)
                }}
              >
                {choice}
              </button>
            ))}
          </div>
        </>
      ) : (
        <div className="wizard-result">
          <h4>{data.diagnosis ?? diagnose(answers)}</h4>
          <p className="muted">
            Use the answers on the left to inspect gas coverage, consumable condition, grounding, and travel technique in that order.
          </p>
          <ul className="answer-list">
            {answers.map((answer, idx) => (
              <li key={idx}>{answer.question} - {answer.choice}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function diagnose(answers) {
  const firstNegative = answers.find(answer => /No/.test(answer.choice))
  if (!firstNegative) {
    return 'Primary causes are less obvious. Recheck gas, contamination, and arc stability with the cited manual steps.'
  }
  return `Most likely issue: ${firstNegative.question.replace('Is ', '').replace('?', '')}.`
}
