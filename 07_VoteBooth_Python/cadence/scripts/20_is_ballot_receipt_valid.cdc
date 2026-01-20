/**
    This script validates is a ballot receipt provided as script argument is a valid one or not, namely, if the receipt provided is among the ones set in the Election with the electionId provided as argument, the script returns true. Otherwise returns false. If the Election in question is not yet finished or the ballot receipt array is not yet set in the instance, the contract function panics with the proper offense.

    @param electionId (UInt64) The election identifier from which the ballot receipt is to be validated to.
    @param ballotReceipt (UInt64) The ballot receipt value to validate.

    @return Bool The script returns true if the ballot receipt provided is among the ones set in the Election identified by the electionId provided. Otherwise returns false. If the Election in question is not yet finished, or the ballotReceipt array not yet set, the script panics instead.
**/
import ElectionStandard from 0x287f5c8b0865c516
import VoteBooth from 0x287f5c8b0865c516

access(all) fun main(electionId: UInt64, ballotReceipt: UInt64): Bool {
    // Grab a public reference to the Election with the electionId provided
    let electionPublicRef: &{ElectionStandard.ElectionPublic} = VoteBooth.getElectionPublicReference(electionId: electionId) ??
    panic(
        "Unable to get a valid &{ElectionStandard.ElectionPublic} from the VoteBooth contract for Election `electionId.toString()`"
    )

    // Don't need to check if the Election is finished or if the ballotReceipts are set. The contract function to execute from the election reference already validates these 
    // elements
    return electionPublicRef.isBallotReceiptValid(ballotReceipt: ballotReceipt)
}