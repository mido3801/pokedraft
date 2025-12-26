import { BracketState, Match } from '../types'

interface BracketDisplayProps {
  bracket: BracketState
  onRecordResult?: (match: Match) => void
}

interface BracketMatchCardProps {
  match: Match
  showResetLabel?: boolean
  onRecordResult?: (match: Match) => void
}

function BracketMatchCard({ match, showResetLabel, onRecordResult }: BracketMatchCardProps) {
  const isComplete = !!match.winner_id
  const isBye = match.is_bye
  const isPending = !match.team_a_id || (!match.team_b_id && !isBye)

  return (
    <div
      className={`bracket-match border rounded-lg p-2 w-48 ${
        isComplete ? 'bg-gray-50' : 'bg-white'
      } ${isPending ? 'opacity-60' : ''}`}
    >
      {showResetLabel && (
        <div className="text-xs text-center text-gray-500 mb-1 italic">(If Necessary)</div>
      )}

      {/* Team A */}
      <div
        className={`flex justify-between items-center p-1.5 rounded text-sm ${
          match.winner_id === match.team_a_id ? 'bg-green-100 font-bold' : ''
        }`}
      >
        <span className="text-xs text-gray-400 w-5">{match.seed_a || '-'}</span>
        <span className="flex-1 truncate px-1">
          {match.team_a_name || (isPending ? 'TBD' : '')}
        </span>
        {isComplete && match.winner_id === match.team_a_id && (
          <span className="text-green-600 text-xs">W</span>
        )}
      </div>

      {/* Divider */}
      <div className="border-t my-1" />

      {/* Team B */}
      <div
        className={`flex justify-between items-center p-1.5 rounded text-sm ${
          match.winner_id === match.team_b_id ? 'bg-green-100 font-bold' : ''
        } ${isBye ? 'text-gray-400 italic' : ''}`}
      >
        <span className="text-xs text-gray-400 w-5">{match.seed_b || '-'}</span>
        <span className="flex-1 truncate px-1">
          {isBye ? 'BYE' : match.team_b_name || (isPending ? 'TBD' : '')}
        </span>
        {isComplete && match.winner_id === match.team_b_id && (
          <span className="text-green-600 text-xs">W</span>
        )}
      </div>

      {/* Action button */}
      {!isComplete && !isPending && !isBye && onRecordResult && (
        <button
          onClick={() => onRecordResult(match)}
          className="w-full mt-2 text-xs text-pokemon-blue hover:underline"
        >
          Record Result
        </button>
      )}

      {match.replay_url && (
        <a
          href={match.replay_url}
          target="_blank"
          rel="noopener noreferrer"
          className="block text-center text-xs text-pokemon-blue hover:underline mt-1"
        >
          Watch Replay
        </a>
      )}
    </div>
  )
}

interface BracketRoundProps {
  roundNumber: number
  roundName: string
  matches: Match[]
  isLosersBracket?: boolean
  onRecordResult?: (match: Match) => void
}

function BracketRound({ roundNumber, roundName, matches, onRecordResult }: BracketRoundProps) {
  // Calculate spacing multiplier for bracket alignment
  // Later rounds have fewer matches, so they need more vertical spacing
  const spacingMultiplier = Math.pow(2, Math.abs(roundNumber) - 1)
  const gap = Math.min(spacingMultiplier * 1.5, 8) // Cap the gap at 8rem

  return (
    <div className="bracket-round flex flex-col items-center min-w-[200px]">
      <div className="round-header text-sm font-medium text-gray-500 text-center mb-3 whitespace-nowrap">
        {roundName}
      </div>
      <div
        className="flex flex-col justify-around flex-1"
        style={{ gap: `${gap}rem` }}
      >
        {matches.map((match) => (
          <BracketMatchCard key={match.id} match={match} onRecordResult={onRecordResult} />
        ))}
      </div>
    </div>
  )
}

export default function BracketDisplay({ bracket, onRecordResult }: BracketDisplayProps) {
  const isDoubleElim = bracket.format === 'double_elimination'

  // Get round name from first match in round, or compute from round number
  const getRoundName = (round: Match[], roundIndex: number, totalRounds: number, isLosers: boolean = false) => {
    if (round[0]?.round_name) {
      return round[0].round_name
    }
    const roundNum = roundIndex + 1
    const roundsFromFinal = totalRounds - roundNum
    const prefix = isLosers ? 'Losers ' : ''
    const names: Record<number, string> = {
      0: 'Finals',
      1: 'Semifinals',
      2: 'Quarterfinals',
      3: 'Round of 16',
      4: 'Round of 32',
    }
    return prefix + (names[roundsFromFinal] || `Round ${roundNum}`)
  }

  return (
    <div className="bracket-container overflow-x-auto pb-4">
      {/* Winners Bracket */}
      <div className="winners-bracket mb-8">
        {isDoubleElim && (
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Winners Bracket</h3>
        )}
        <div className="flex gap-8 items-stretch">
          {bracket.winners_bracket.map((round, roundIdx) => (
            <BracketRound
              key={`winners-${roundIdx}`}
              roundNumber={roundIdx + 1}
              roundName={getRoundName(round, roundIdx, bracket.total_rounds)}
              matches={round}
              onRecordResult={onRecordResult}
            />
          ))}
        </div>
      </div>

      {/* Grand Finals (double elim only) */}
      {isDoubleElim && bracket.grand_finals && bracket.grand_finals.length > 0 && (
        <div className="grand-finals my-8 pt-8 border-t">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Grand Finals</h3>
          <div className="flex gap-8 justify-center">
            {bracket.grand_finals.map((match) => (
              <BracketMatchCard
                key={match.id}
                match={match}
                showResetLabel={match.is_bracket_reset}
                onRecordResult={onRecordResult}
              />
            ))}
          </div>
        </div>
      )}

      {/* Losers Bracket (double elim only) */}
      {isDoubleElim && bracket.losers_bracket && bracket.losers_bracket.length > 0 && (
        <div className="losers-bracket mt-8 pt-8 border-t">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Losers Bracket</h3>
          <div className="flex gap-8 items-stretch">
            {bracket.losers_bracket.map((round, roundIdx) => (
              <BracketRound
                key={`losers-${roundIdx}`}
                roundNumber={roundIdx + 1}
                roundName={getRoundName(round, roundIdx, bracket.losers_bracket!.length, true)}
                matches={round}
                isLosersBracket
                onRecordResult={onRecordResult}
              />
            ))}
          </div>
        </div>
      )}

      {/* Champion banner */}
      {bracket.champion_id && bracket.champion_name && (
        <div className="champion-banner mt-8 p-6 bg-gradient-to-r from-yellow-100 to-yellow-200 rounded-lg text-center border-2 border-yellow-400">
          <div className="text-2xl mb-2">Champion</div>
          <div className="text-3xl font-bold text-yellow-800">{bracket.champion_name}</div>
        </div>
      )}
    </div>
  )
}
