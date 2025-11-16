/**
    This script retrieves the list of results from the election identified by the electionId provided and computes the winner(s), i.e., all options that gathered the most votes, even if equal, are returned from this script.

    @param electionId (UInt64) The election identifier from which the election winner is to be retrieved.

    @return [{String: Int}] This script returns an array with the dictionary entries, in a {electionBallot: ballotCount} format. If more than one Election options wins, this script returns all of them.
**/
import ElectionStandard from 0xf8d6e0586b0a20c7
import VoteBooth from 0xf8d6e0586b0a20c7

access(all) fun main(electionId: UInt64): {String:Int} {
    let electionPublicRef: &{ElectionStandard.ElectionPublic} = VoteBooth.getElectionPublicReference(electionId: electionId) ??
    panic(
        "Unable to get a valid &{ElectionStandard.ElectionPublic} from the VoteBooth contract for election "
        .concat(electionId.toString())
    )

    if (!electionPublicRef.isElectionFinished()) {
        // Return an empty result set if the election is not yet finished
        return {}
    }

    let electionResults: {String: Int} = electionPublicRef.getElectionTally()

    var winningOptions: {String: Int} = {}
    var currentWinner: {String: Int}? = nil
    // Cycle through all the election options and extract the winning one(s)

    for result in electionResults.keys {
        // If there's no temp winner set yet or the current record has more votes than the current temp winner
        if (currentWinner == nil || electionResults[result]! > currentWinner!.values[0]) {
            // Set the new temp winner as the current record
            currentWinner = {result: electionResults[result]!}

            // And set the winning options for this record for now, clearing any previous sets
            winningOptions = currentWinner!
        }

        // If I found a tie between the current temp winner and the current record
        if (currentWinner != nil && electionResults[result]! == currentWinner!.values[0]) {
            // Add the new winning option to the current set. No need to set a new winner because the total votes are still the same
            winningOptions[result] = electionResults[result]!
        }
    }
    
    // All done. Return the election results back.
    return winningOptions
}