/**
    This script retrieved and returns the array of encrypted options from an already tallied election. Otherwise it returns an empty array because that's the state of it before the election is tallied.

    @param electionId (UInt64) The election identifier from which the encrypted options are to be retrieved.

    @returns [String] Return the array of encrypted options as set in the election in question.
**/

import "ElectionStandard"
import "VoteBooth"

access(all) fun main(electionId: UInt64): [String] {
    let electionPublicRef: &{ElectionStandard.ElectionPublic} = VoteBooth.getElectionPublicReference(electionId: electionId) ??
    panic(
        "Unable to get a valid &{ElectionStandard.ElectionPublic} from the VoteBooth contract for election "
        .concat(electionId.toString())
    )

    return electionPublicRef.getEncryptedOptions()
}