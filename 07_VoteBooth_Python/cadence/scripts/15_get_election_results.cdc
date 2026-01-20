/**
    Simple script to return the tally results for a given election. If the Election is not yet finished, this array is empty and that's what this script is going to return.

    @param electionId (UInt64) The election identifier from which the election results are to be returned.
**/

import ElectionStandard from 0x287f5c8b0865c516
import VoteBooth from 0x287f5c8b0865c516

access(all) fun main(electionId: UInt64): {String: Int} {

    let electionPublicRef: &{ElectionStandard.ElectionPublic} = VoteBooth.getElectionPublicReference(electionId: electionId) ??
    panic(
        "Unable to get a valid &{ElectionStandard.ElectionPublic} from the VoteBooth contract for election `electionId.toString()`"
    )

    return electionPublicRef.getElectionResults()
}